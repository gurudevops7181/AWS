import json
import logging
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client("ec2")
cloudwatch_client = boto3.client("cloudwatch")
elbv2_client = boto3.client("elbv2")
sns_client = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")


def _load_configuration():
    try:
        target_group_arns = json.loads(os.environ["TARGET_GROUP_ARNS"])
    except KeyError as error:
        raise ValueError(f"Missing required environment variable: {error.args[0]}")
    except json.JSONDecodeError as error:
        raise ValueError("TARGET_GROUP_ARNS must contain a JSON object.") from error

    if not isinstance(target_group_arns, dict) or not target_group_arns:
        raise ValueError("TARGET_GROUP_ARNS must be a non-empty JSON object.")

    required = ("SNS_TOPIC_ARN", "UNHEALTHY_TARGETS_TABLE")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError(
            "Missing required environment variable(s): " + ", ".join(missing)
        )

    return target_group_arns, os.environ["SNS_TOPIC_ARN"], os.environ[
        "UNHEALTHY_TARGETS_TABLE"
    ]


def _get_alarm_state(alarm_message, alarm_name):
    # CloudWatch alarm SNS notifications include NewStateValue. Keep the API
    # lookup as a fallback for manually generated or older event payloads.
    state = alarm_message.get("NewStateValue")
    if state:
        return state

    response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    alarms = response.get("MetricAlarms", [])
    return alarms[0].get("StateValue", "UNKNOWN") if alarms else "UNKNOWN"


def _get_private_ip(target_id):
    if not target_id.startswith("i-"):
        return target_id

    response = ec2_client.describe_instances(InstanceIds=[target_id])
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            if instance.get("InstanceId") == target_id:
                return instance.get("PrivateIpAddress", target_id)
    return target_id


def _stored_target_ids(table, alarm_name):
    target_ids = set()
    query_args = {
        "KeyConditionExpression": Key("alarm_name").eq(alarm_name),
        "ProjectionExpression": "#target_id",
        "ExpressionAttributeNames": {"#target_id": "target_id"},
    }

    while True:
        response = table.query(**query_args)
        target_ids.update(item["target_id"] for item in response.get("Items", []))
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            return target_ids
        query_args["ExclusiveStartKey"] = last_key


def _delete_target_ids(table, alarm_name, target_ids):
    for target_id in target_ids:
        table.delete_item(
            Key={"alarm_name": alarm_name, "target_id": target_id}
        )


def _clear_alarm_state(table, alarm_name):
    _delete_target_ids(table, alarm_name, _stored_target_ids(table, alarm_name))


def _remember_new_target(table, alarm_name, target_group_arn, target_id, timestamp):
    try:
        table.put_item(
            Item={
                "alarm_name": alarm_name,
                "target_group_arn": target_group_arn,
                "target_id": target_id,
                "notified_at": timestamp,
            },
            ConditionExpression=(
                "attribute_not_exists(#alarm_name) "
                "AND attribute_not_exists(#target_id)"
            ),
            ExpressionAttributeNames={
                "#alarm_name": "alarm_name",
                "#target_id": "target_id",
            },
        )
        return True
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return False
        raise


def _process_alarm(alarm_message, target_group_arns, sns_topic_arn, table):
    alarm_name = alarm_message.get("AlarmName")
    if not alarm_name:
        raise ValueError("SNS alarm message is missing AlarmName.")

    target_group_arn = target_group_arns.get(alarm_name)
    if not target_group_arn:
        logger.warning("No target group configured for alarm %s; skipping.", alarm_name)
        return []

    alarm_state = _get_alarm_state(alarm_message, alarm_name)
    if alarm_state == "OK":
        _clear_alarm_state(table, alarm_name)
        return []
    if alarm_state != "ALARM":
        logger.info("Alarm %s is in state %s; skipping.", alarm_name, alarm_state)
        return []

    response = elbv2_client.describe_target_health(
        TargetGroupArn=target_group_arn
    )
    unhealthy_descriptions = [
        description
        for description in response.get("TargetHealthDescriptions", [])
        if description.get("TargetHealth", {}).get("State") == "unhealthy"
    ]
    current_unhealthy_ids = {
        description["Target"]["Id"] for description in unhealthy_descriptions
    }

    previously_notified_ids = _stored_target_ids(table, alarm_name)
    _delete_target_ids(
        table,
        alarm_name,
        previously_notified_ids - current_unhealthy_ids,
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    candidates = []
    for description in unhealthy_descriptions:
        target_id = description["Target"]["Id"]
        candidates.append(
            {
                "target_id": target_id,
                "private_ip": _get_private_ip(target_id),
                "reason": description["TargetHealth"].get("Reason", "unknown"),
                "description": description["TargetHealth"].get(
                    "Description", "No health description"
                ),
            }
        )

    newly_unhealthy = []
    claimed_ids = set()
    try:
        for target in candidates:
            if _remember_new_target(
                table, alarm_name, target_group_arn, target["target_id"], timestamp
            ):
                claimed_ids.add(target["target_id"])
                newly_unhealthy.append(target)

        if not newly_unhealthy:
            return []

        message_lines = [
            f"New unhealthy targets detected for alarm {alarm_name}.",
            f"Target group: {target_group_arn}",
            f"Alarm state: {alarm_state}",
            f"Timestamp: {timestamp}",
            "",
        ]
        for target in newly_unhealthy:
            message_lines.extend(
                [
                    f"Target ID: {target['target_id']}",
                    f"Private IP: {target['private_ip']}",
                    f"Reason: {target['reason']}",
                    f"Description: {target['description']}",
                    "",
                ]
            )

        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message="\n".join(message_lines),
            Subject="New Unhealthy Targets in Target Group",
        )
    except Exception:
        # Allow a retried Lambda invocation to claim these targets again.
        try:
            _delete_target_ids(table, alarm_name, claimed_ids)
        except Exception:
            logger.exception(
                "Failed to clear notification state for alarm %s.", alarm_name
            )
        raise

    return newly_unhealthy


def lambda_handler(event, context):
    target_group_arns, sns_topic_arn, table_name = _load_configuration()
    table = dynamodb.Table(table_name)
    newly_unhealthy = []

    for record in event.get("Records", []):
        alarm_message = json.loads(record["Sns"]["Message"])
        newly_unhealthy.extend(
            _process_alarm(alarm_message, target_group_arns, sns_topic_arn, table)
        )

    return {
        "statusCode": 200,
        "body": json.dumps({"newly_unhealthy_targets": newly_unhealthy}),
    }
