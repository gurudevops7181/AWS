# AWS Lambda Automation Suite

Independent Python tools for EC2 scheduling, load balancer target management,
and target health notifications.

## Modules

| Module | Purpose | Documentation |
| --- | --- | --- |
| EC2 start/stop scheduler | Starts and stops tagged instances on an EventBridge schedule. | [README](./lambda/Schedule-start-stop-ec2/README.md) |
| Scheduled target deregistration | Deregisters configured targets during a time window. | [README](./lambda/schedule-Deregister/README.md) |
| Scheduled target registration | Registers configured targets during a time window. | [README](./lambda/schedule-Register/README.md) |
| Unhealthy target notifications | Sends SNS alerts for newly unhealthy targets. | [README](./lambda/unhealthy-target-groups/README.md) |
| Find target groups by IP | Finds target groups containing one or more IP addresses. | [README](./find-elb-target-by-ip/README.md) |

## GitHub Actions

The [scheduled target deregistration workflow](./.github/workflows/schedule-deregister.yml)
runs daily on a `self-hosted` runner at 10:50, 10:55, and 11:00 IST. It can
also be started manually from the Actions tab. The runner needs AWS credentials
with the permissions described in the [deregistration guide](./lambda/schedule-Deregister/README.md).

## Runtime and deployment

The Lambda examples target Python 3.13. Choose a currently supported managed
runtime when deploying, and validate the code and dependencies before changing
an existing function's runtime.

Each module has a requirements.txt with its Boto3 and Botocore versions.
Include the module's Python file and installed dependencies in the deployment
package. The registration and deregistration functions also need
target_instances.txt beside the Python file in that package.

The unhealthy-target monitor requires a DynamoDB table and the environment
variables described in its README. IAM permissions and event sources are
configured in AWS; this repository does not include infrastructure-as-code.

The find-elb-target-by-ip command line tool uses the AWS profile and region
configured on the machine where it runs.
