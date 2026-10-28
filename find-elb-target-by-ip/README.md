# Find ELB target groups by private IP

This read-only command line tool searches target groups in the AWS profile's
configured region and reports any registered targets matching the supplied
private IP addresses. It supports instance and IP target groups.

The script paginates target groups and batches EC2 lookups for instance
targets. It reports every matching target group and prints a message when no
matches are found.

## Requirements

- Python 3.13 or 3.14
- AWS CLI credentials and a configured region for the selected profile
- IAM permissions:
  - elasticloadbalancing:DescribeTargetGroups
  - elasticloadbalancing:DescribeTargetHealth
  - ec2:DescribeInstances

Install the pinned dependencies from this directory:

    python -m pip install -r requirements.txt

Run:

    python find_target_by_ip.py <aws_profile_name> <private_ip1> [<private_ip2> ...]

Example:

    python find_target_by_ip.py prod-profile 10.0.1.15 10.0.5.22

The command uses the region configured for that profile. Run it again with a
different profile or region to search a different AWS account or region.
