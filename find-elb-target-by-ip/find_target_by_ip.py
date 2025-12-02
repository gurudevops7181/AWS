import boto3
import sys

def find_targets(profile_name, private_ips):
    session = boto3.Session(profile_name=profile_name)
    elbv2 = session.client('elbv2')

    # Get all target groups
    response = elbv2.describe_target_groups()
    target_groups = response['TargetGroups']

    print(f"\nSearching across {len(target_groups)} target groups...\n")

    for tg in target_groups:
        tg_arn = tg['TargetGroupArn']
        tg_name = tg['TargetGroupName']
        tg_type = tg.get('TargetType', 'instance')

        targets = elbv2.describe_target_health(TargetGroupArn=tg_arn)['TargetHealthDescriptions']

        for t in targets:
            target = t['Target']
            target_ip = target.get('Id') if tg_type == 'ip' else None
            target_id = target.get('Id') if tg_type == 'instance' else None

            # Instance target type → resolve private IP
            if tg_type == 'instance':
                ec2 = session.client('ec2')
                instance = ec2.describe_instances(InstanceIds=[target_id])
                private_ip = instance['Reservations'][0]['Instances'][0]['PrivateIpAddress']

                if private_ip in private_ips:
                    print(f"✅ Found match: {private_ip} → TargetGroup: {tg_name} ({tg_type})")
                    print(f"   Instance ID: {target_id}")
                    break

            # IP target type
            elif tg_type == 'ip' and target_ip in private_ips:
                print(f"✅ Found match: {target_ip} → TargetGroup: {tg_name} ({tg_type})")
                break


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python find_target_by_ip.py <aws_profile_name> <private_ip1> [<private_ip2> ...]")
        sys.exit(1)

    profile = sys.argv[1]
    ips = sys.argv[2:]

    find_targets(profile, ips)
