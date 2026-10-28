# Scheduled target registration

This Lambda reads target group ARNs, EC2 instance IDs, and schedule keys from
target_instances.txt. During a configured IST time window, it registers the
targets with their target groups. It supports target groups with instance and
IP target types; for IP target groups, the script resolves each EC2 instance's
private IP.

## Configuration

Keep target_instances.txt beside schedule-Register.py, and include both files
in the Lambda deployment package. Each non-comment line uses this format:

    [target-group-arn][instance-id,instance-id][schedule-key]

Example only:

    [arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/example/abc123][i-0123456789abcdef0][16:00]

The schedule key must exist in start_tag_times in schedule-Register.py. The
example key 16:00 currently runs from 16:00 through 16:59 IST, inclusive. Add
or edit entries in that dictionary to define other windows.

The function may be invoked repeatedly during a window. Before registering,
it checks target health and only submits targets that are not already in the
target group.

## Deployment

Use a currently supported Python Lambda runtime; Python 3.13 is the documented
target for this repository. Include schedule-Register.py, target_instances.txt,
and the dependencies from requirements.txt in the deployment package.

The Lambda execution role needs these permissions:

- elasticloadbalancing:DescribeTargetGroups
- elasticloadbalancing:DescribeTargetHealth
- elasticloadbalancing:RegisterTargets
- ec2:DescribeInstances

Run locally from this directory with python schedule-Register.py. The
configured AWS credentials and region will be used, and the command can change
real target group registrations.

File and AWS API errors are raised to Lambda so the configured invocation
retry policy can handle them.

## Example schedule

The current code contains a 16:00 schedule key with a 16:00–16:59 IST window.
Configure EventBridge to invoke the function during that period. Update both
the file entries and the start_tag_times dictionary when adding schedules.
