# Unhealthy target notifications

This Lambda receives CloudWatch alarm notifications through SNS, checks the
mapped target group's health, and sends an SNS message for each newly unhealthy
target. It supports instance and IP targets. Instance targets are resolved to
their EC2 private IP for the notification.

The function uses DynamoDB to remember which targets have already been
notified. Duplicate alarm events do not repeat alerts. State is cleared when
the alarm returns to OK or a target is no longer unhealthy, so a later failure
can produce a new alert.

## Lambda configuration

Set these environment variables:

- TARGET_GROUP_ARNS: JSON object mapping each CloudWatch alarm name to a target
  group ARN.
- SNS_TOPIC_ARN: ARN of the topic that receives the outgoing notifications.
- UNHEALTHY_TARGETS_TABLE: name of the DynamoDB table used for deduplication.

Example TARGET_GROUP_ARNS value:

    {"UnHealthyHostCount-my-target-group":"arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/my-target-group/abcd1234"}

The DynamoDB table must have a string partition key named alarm_name and a
string sort key named target_id. The function stores the mapped target group
ARN and a notified_at timestamp with each target. State is tracked per alarm.

Configure each CloudWatch alarm to publish to an input SNS topic, then
subscribe this Lambda to that topic. Use a separate topic for SNS_TOPIC_ARN;
publishing back to the input topic can trigger the function recursively.

## IAM permissions

Grant the Lambda execution role:

- elasticloadbalancing:DescribeTargetHealth
- ec2:DescribeInstances
- cloudwatch:DescribeAlarms (fallback for alarm messages without NewStateValue)
- dynamodb:Query
- dynamodb:PutItem
- dynamodb:DeleteItem
- sns:Publish

Scope DynamoDB actions to the deduplication table and sns:Publish to the
outgoing SNS topic ARN.

## Deployment

Use a currently supported Python Lambda runtime; Python 3.13 is the documented
target for this repository. Include unhealthy-target-groups.py and the
dependencies from requirements.txt in the deployment package.

The code reads alarm names and target group ARNs from environment variables;
there are no placeholder ARNs or SNS topic names in the Python file.
Processing and publish errors are raised so the Lambda/SNS retry policy can
retry the alarm notification.
