# Scheduled target deregistration

This Lambda reads target group ARNs, EC2 instance IDs, and schedule keys from
target_instances.txt. During a configured IST time window, it deregisters the
targets from their target groups. It supports target groups with instance and
IP target types; for IP target groups, the script resolves each EC2 instance's
private IP.

## Configuration

Keep target_instances.txt beside schedule-Deregister.py, and include both
files in the Lambda deployment package. Each non-comment line uses this format:

    [target-group-arn][instance-id,instance-id][schedule-key]

Example only:

    [arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/example/abc123][i-0123456789abcdef0][10:50]

The schedule key must exist in start_tag_times in schedule-Deregister.py. The
example key 10:50 currently runs from 10:50 through 11:00 IST, inclusive. Add
or edit entries in that dictionary to define other windows.

The function may be invoked repeatedly during a window. Before deregistering,
it checks target health and only submits targets that are registered and not
already draining. Targets in draining state are left to finish draining.

## Deployment

Use a currently supported Python Lambda runtime; Python 3.13 is the documented
target for this repository. Include schedule-Deregister.py, target_instances.txt,
and the dependencies from requirements.txt in the deployment package.

The Lambda execution role needs these permissions:

- elasticloadbalancing:DescribeTargetGroups
- elasticloadbalancing:DescribeTargetHealth
- elasticloadbalancing:DeregisterTargets
- ec2:DescribeInstances

Run locally from this directory with python schedule-Deregister.py. The
configured AWS credentials and region will be used, and the command can change
real target group registrations.

File and AWS API errors are raised to Lambda so the configured invocation
retry policy can handle them.

## Example schedule

The current code contains a 10:50 schedule key with a 10:50–11:00 IST window.
Configure EventBridge to invoke the function during that period. Update both
the file entries and the start_tag_times dictionary when adding schedules.

## GitHub Actions workflow

The repository workflow at `.github/workflows/schedule-deregister.yml` runs
this script on the `self-hosted` runner at 10:50, 10:55, and 11:00 IST, and can
also be started manually from the Actions tab. It sets the AWS region to
`ap-south-1`; the runner must have AWS credentials with the permissions listed
above. The script still checks its configured IST window, so manual runs
outside that window do not deregister targets.
