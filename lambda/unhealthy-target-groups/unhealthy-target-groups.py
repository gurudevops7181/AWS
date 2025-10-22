import boto3
from datetime import datetime
import json

ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')
elbv2_client = boto3.client('elbv2')
sns_client = boto3.client('sns')

def get_private_ip(instance_id_or_ip):
    if instance_id_or_ip.startswith('i-'):
        response = ec2_client.describe_instances(InstanceIds=[instance_id_or_ip])
        instances = response.get('Reservations', [])[0].get('Instances', [])
        if instances:
            return instances[0].get('PrivateIpAddress')
    return instance_id_or_ip

def get_alarm_state(alarm_name):
    response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    alarms = response.get('MetricAlarms', [])
    if alarms:
        state_value = alarms[0]['StateValue']
        state_updated_timestamp = alarms[0]['StateUpdatedTimestamp'].isoformat() if 'StateUpdatedTimestamp' in alarms[0] else None
        return state_value, state_updated_timestamp
    return 'UNKNOWN', None

def lambda_handler(event, context):
    unhealthy_instances = []  # Initialize the variable here
    target_group_arns = {
        'cloudwatch alarm-name': "Target-group-arn", #need to add the here cloudwatch alarm name and target-group arn
    }
    previous_unhealthy_instance_ids = getattr(context, 'previous_unhealthy_instance_ids', set())

    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        alarm_name = sns_message['AlarmName']
        target_group_arn = target_group_arns.get(alarm_name)
        sns_topic_arn = "SNS-TOPIC-NAME"  # need to add sns topic name 

        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)

        for target in response.get('TargetHealthDescriptions', []):
            if target['TargetHealth']['State'] == 'unhealthy':
                instance_id = target['Target']['Id']
                private_ip = get_private_ip(instance_id)
                alarm_name = f"{target_group_arn.split('/')[1]}-UnHealthyHostCount"
                alarm_state, alarm_timestamp = get_alarm_state(alarm_name)

                if alarm_state == 'ALARM':
                    unhealthy_instances.append({
                        'target_group_arn': target_group_arn,
                        'id': instance_id,
                        'private_ip': private_ip,
                        'alarm_state': alarm_state,
                        'timestamp': alarm_timestamp or datetime.now().isoformat()
                    })

    new_unhealthy_instance_ids = set(instance['id'] for instance in unhealthy_instances) - previous_unhealthy_instance_ids

    if new_unhealthy_instance_ids:
        message = f"New unhealthy instances detected with Alarm State ALARM:\n"
        unhealthy_instances.sort(key=lambda x: x['timestamp'], reverse=True)
        for instance in unhealthy_instances:
            message += f"\nTarget Group: {instance['target_group_arn']}\nID: {instance['id']}\nPrivate IP: {instance['private_ip']}\nAlarm State: {instance['alarm_state']}\nTimestamp: {instance['timestamp']}\n"

        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject="New Unhealthy Instances in Target Groups"
        )

        print(f"New unhealthy instances with Alarm State ALARM detected. Message published to SNS topic: {sns_topic_arn}")

    setattr(context, 'previous_unhealthy_instance_ids', set(instance['id'] for instance in unhealthy_instances))

    return {
        'statusCode': 200,
        'body': {
            'unhealthy_instances': unhealthy_instances
        }
    }