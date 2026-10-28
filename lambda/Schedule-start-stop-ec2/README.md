# EC2 start/stop scheduler

This Lambda starts and stops EC2 instances based on their tags and the current
time in India Standard Time (IST). Schedule the function with EventBridge,
typically every five minutes.

## Tags and schedule windows

The tag keys are scheduleStart and scheduleStop. Tag values must match a key in
the corresponding schedule dictionary in Schedule-start-stop-ec2.py. For
example:

| Action | Tag key | Tag value | Time window |
| --- | --- | --- | --- |
| Start | scheduleStart | ST-10:00 | 10:00 up to, but not including, 10:05 IST |
| Stop | scheduleStop | SD-22:00 | 22:00 up to, but not including, 22:05 IST |

The windows are half-open so an invocation at 10:05 matches the next slot,
not both adjacent slots. Add or edit entries in start_tag_times and
stop_tag_times to define other windows.

## Deployment

Use a currently supported Python Lambda runtime; Python 3.13 is the documented
target for this repository. Include Schedule-start-stop-ec2.py and the
dependencies from requirements.txt in the deployment package.

Grant the function these EC2 permissions, scoped to the resources supported by
the EC2 APIs:

- ec2:DescribeInstances
- ec2:StartInstances
- ec2:StopInstances

The function uses the Lambda region automatically. For local use, configure
AWS credentials and a default region, then run python Schedule-start-stop-ec2.py
from this directory.

Running the script can start or stop real EC2 instances in the selected
account and region.

## EventBridge schedule

Create an EventBridge schedule with rate(5 minutes) and grant it permission
to invoke the Lambda function. The Lambda must run at least once during each
configured five-minute window. Instance operation failures are raised to
Lambda; configure an appropriate retry policy and dead-letter destination for
failed invocations.
