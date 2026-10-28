import boto3
from datetime import datetime, timezone, timedelta
import re
from pathlib import Path

# Initialize the boto3 clients
elbv2_client = boto3.client('elbv2')
ec2_client = boto3.client('ec2')

# Set IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

def get_target_type(target_group_arn):
    """Retrieves the target type (instance/ip) of a target group."""
    try:
        response = elbv2_client.describe_target_groups(TargetGroupArns=[target_group_arn])
        target_type = response['TargetGroups'][0]['TargetType']
        return target_type
    except Exception as e:
        raise Exception(f"Error getting target group type for {target_group_arn}: {e}")

def get_instance_private_ip(instance_id):
    """Gets the private IP address of an EC2 instance."""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        private_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        return private_ip
    except Exception as e:
        raise Exception(f"Error getting private IP for instance {instance_id}: {e}")

def deregister_instances_from_target_group(target_group_arn, instance_ids):
    """Deregisters instances from a target group based on target type."""
    try:
        target_type = get_target_type(target_group_arn)

        targets = []
        if target_type == 'instance':
            targets = [{'Id': instance_id} for instance_id in dict.fromkeys(instance_ids)]
        elif target_type == 'ip':
            targets = [
                {'Id': get_instance_private_ip(instance_id)}
                for instance_id in dict.fromkeys(instance_ids)
            ]
        else:
            raise ValueError("Unsupported target type.")

        health_response = elbv2_client.describe_target_health(
            TargetGroupArn=target_group_arn
        )
        registered_ids = {
            description['Target']['Id']
            for description in health_response.get('TargetHealthDescriptions', [])
            if description.get('TargetHealth', {}).get('State') != 'draining'
        }
        targets = [target for target in targets if target['Id'] in registered_ids]
        if not targets:
            print(f"No requested targets are currently registered in {target_group_arn}.")
            return None

        response = elbv2_client.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=targets
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"Targets {targets} deregistered from target group {target_group_arn}.")
        else:
            print(f"Failed to deregister targets {targets} from target group {target_group_arn}.")
        
        return response
    except Exception as e:
        raise Exception(f"Error deregistering instances from target group {target_group_arn}: {e}")

def time_in_range(start_time, end_time, check_time):
    """
    Check if the current time falls between a start and end time.
    """
    return start_time <= check_time <= end_time

def process_file_for_deregister(file_content):
    """Processes the input content containing target group ARNs, instance IDs, and scheduled times."""
    target_group_to_instances = {}

    # Get current time in IST
    now = datetime.now(IST)
    current_time = now.strftime('%H:%M')  # Current time in HH:MM format
    print(f"Current IST time: {current_time}")

    # Define the start time ranges
    start_tag_times = {
        '10:50': ('10:50', '11:00'),
        # Add more time slots if needed
    }

    for line in file_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        match = re.fullmatch(r'\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\]', line)
        if not match:
            print(f"Skipping invalid configuration line: {line}")
            continue

        target_group_arn = match.group(1).strip()
        instance_ids = [
            instance_id.strip()
            for instance_id in match.group(2).split(',')
            if instance_id.strip()
        ]
        scheduled_time = match.group(3).strip()
        if not instance_ids:
            print(f"Skipping configuration with no instance IDs: {line}")
            continue

        # Check if the scheduled time falls within the current time range
        if scheduled_time in start_tag_times:
            start_time, end_time = start_tag_times[scheduled_time]
            if time_in_range(start_time, end_time, current_time):
                print(f"Current time {current_time} is within the range {start_time} - {end_time} for deregistration.")
                if target_group_arn in target_group_to_instances:
                    target_group_to_instances[target_group_arn].extend(instance_ids)
                else:
                    target_group_to_instances[target_group_arn] = instance_ids
            else:
                print(f"Current time {current_time} does not fall within the scheduled time range {start_time} - {end_time}.")
        else:
            print(f"Scheduled time {scheduled_time} does not have a defined range.")

    for target_group_arn, instance_ids in target_group_to_instances.items():
        deregister_instances_from_target_group(target_group_arn, instance_ids)

def lambda_handler(event, context):
    """Lambda handler function."""
    # Keep the configuration beside the function so the same path works locally
    # and when both files are included in the Lambda deployment package.
    file_path = Path(__file__).with_name('target_instances.txt')

    try:
        with file_path.open('r', encoding='utf-8') as file:
            file_content = file.read()
    except Exception as e:
        raise RuntimeError(f"Error reading {file_path}: {e}") from e

    process_file_for_deregister(file_content)

    return {
        'statusCode': 200,
        'body': 'Deregistration completed.'
    }

# This makes the script runnable for testing (optional)
if __name__ == '__main__':
    lambda_handler(None, None)
