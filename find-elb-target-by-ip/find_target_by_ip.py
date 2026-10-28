import sys

import boto3


def _chunks(items, size=200):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def find_targets(profile_name, private_ips):
    requested_ips = set(private_ips)
    if not requested_ips:
        raise ValueError("Provide at least one private IP address.")

    session = boto3.Session(profile_name=profile_name)
    elbv2 = session.client("elbv2")
    ec2 = session.client("ec2")

    target_group_paginator = elbv2.get_paginator("describe_target_groups")
    target_groups = [
        target_group
        for page in target_group_paginator.paginate()
        for target_group in page.get("TargetGroups", [])
    ]
    print(f"\nSearching across {len(target_groups)} target groups...\n")

    health_by_arn = {}
    for target_group in target_groups:
        target_group_arn = target_group["TargetGroupArn"]
        health_by_arn[target_group_arn] = elbv2.describe_target_health(
            TargetGroupArn=target_group_arn
        ).get("TargetHealthDescriptions", [])

    # Resolve all instance targets in batches instead of making one EC2 request
    # per target. The instance-id filter safely ignores targets whose instances
    # have already been terminated.
    instance_ids = sorted(
        {
            health_description["Target"]["Id"]
            for target_group in target_groups
            if target_group.get("TargetType") == "instance"
            for health_description in health_by_arn[target_group["TargetGroupArn"]]
        }
    )
    private_ip_by_instance_id = {}
    instance_paginator = ec2.get_paginator("describe_instances")
    for id_batch in _chunks(instance_ids):
        for page in instance_paginator.paginate(
            Filters=[{"Name": "instance-id", "Values": id_batch}]
        ):
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    private_ip = instance.get("PrivateIpAddress")
                    if private_ip:
                        private_ip_by_instance_id[instance["InstanceId"]] = private_ip

    matches = {private_ip: [] for private_ip in requested_ips}
    for target_group in target_groups:
        target_group_arn = target_group["TargetGroupArn"]
        target_group_name = target_group["TargetGroupName"]
        target_type = target_group.get("TargetType", "instance")
        for health_description in health_by_arn[target_group_arn]:
            target_id = health_description["Target"].get("Id")
            if target_type == "ip":
                private_ip = target_id
            elif target_type == "instance":
                private_ip = private_ip_by_instance_id.get(target_id)
            else:
                continue

            if private_ip in matches:
                matches[private_ip].append(
                    (target_group_name, target_type, target_id)
                )

    found_any = False
    for private_ip in private_ips:
        for target_group_name, target_type, target_id in matches[private_ip]:
            found_any = True
            print(
                f"✅ Found match: {private_ip} → TargetGroup: "
                f"{target_group_name} ({target_type})"
            )
            if target_type == "instance":
                print(f"   Instance ID: {target_id}")
    if not found_any:
        print("No matching targets found.")

    return matches


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python find_target_by_ip.py "
            "<aws_profile_name> <private_ip1> [<private_ip2> ...]"
        )
        sys.exit(1)

    find_targets(sys.argv[1], sys.argv[2:])
