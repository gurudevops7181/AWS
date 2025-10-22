import boto3
from datetime import datetime, timezone, timedelta
import re

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

def register_instances_to_target_group(target_group_arn, instance_ids):
    """Registers instances to a target group based on target type."""
    try:
        target_type = get_target_type(target_group_arn)

        targets = []
        if target_type == 'instance':
            targets = [{'Id': instance_id} for instance_id in instance_ids]
        elif target_type == 'ip':
            targets = [{'Id': get_instance_private_ip(instance_id)} for instance_id in instance_ids]
        else:
            raise ValueError("Unsupported target type.")

        response = elbv2_client.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=targets
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"Targets {targets} registered to target group {target_group_arn}.")
        else:
            print(f"Failed to register targets {targets} to target group {target_group_arn}.")
        
        return response
    except Exception as e:
        raise Exception(f"Error registering instances to target group {target_group_arn}: {e}")

def time_in_range(start_time, end_time, check_time):
    """
    Check if the current time falls between a start and end time.
    """
    return start_time <= check_time <= end_time

def process_file_for_register(file_content):
    """Processes the input content containing target group ARNs, instance IDs, and scheduled times."""
    target_group_to_instances = {}

    # Get current time in IST
    now = datetime.now(IST)
    current_time = now.strftime('%H:%M')  # Current time in HH:MM format
    print(f"Current IST time: {current_time}")

    # Define the start time ranges
    start_tag_times = {
        '16:00': ('16:00', '16:59'),
        # Add more time slots if needed
    }

    for line in file_content.strip().split('\n'):
        match = re.match(r'\[(.*?)\]\[(.*?)\]\[(.*?)\]', line.strip())
        if match:
            target_group_arn = match.group(1)
            instance_ids = match.group(2).split(',')
            scheduled_time = match.group(3)

            # Check if the scheduled time falls within the current time range
            if scheduled_time in start_tag_times:
                start_time, end_time = start_tag_times[scheduled_time]
                if time_in_range(start_time, end_time, current_time):
                    print(f"Current time {current_time} is within the range {start_time} - {end_time} for registration.")
                    if target_group_arn in target_group_to_instances:
                        target_group_to_instances[target_group_arn].extend(instance_ids)
                    else:
                        target_group_to_instances[target_group_arn] = instance_ids
                else:
                    print(f"Current time {current_time} does not fall within the scheduled time range {start_time} - {end_time}.")
            else:
                print(f"Scheduled time {scheduled_time} does not have a defined range.")

    for target_group_arn, instance_ids in target_group_to_instances.items():
        register_instances_to_target_group(target_group_arn, instance_ids)

def lambda_handler(event, context):
    """Lambda handler function."""
    # Read the file content from the Lambda's environment (assuming the file is in the /tmp directory)
    file_path = 'target_instances.txt'

    try:
        with open(file_path, 'r') as file:
            file_content = file.read()
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error reading file from Lambda environment: {e}"
        }

    # Process the file content
    try:
        process_file_for_register(file_content)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error processing file: {e}"
        }

    return {
        'statusCode': 200,
        'body': 'Registration completed.'
    }

# This makes the script runnable for testing (optional)
if __name__ == '__main__':
    lambda_handler(None, None)
