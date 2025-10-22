import boto3
from datetime import datetime, timezone, timedelta

# Initialize EC2 resource
ec2 = boto3.resource('ec2', region_name='ap-south-1')

# Tag keys
start_tag_key = 'scheduleStart'
stop_tag_key = 'scheduleStop'

def print_instances_by_tag(key, value):
    instances = ec2.instances.filter(
        Filters=[{'Name': f'tag:{key}', 'Values': [value]}]
    )
    instance_details = [(instance.id, instance.state['Name']) for instance in instances]
    
    if instance_details:
        print(f"[INFO] Instances with tag '{key}={value}': {[id for id, _ in instance_details]}")
        return instance_details
    else:
        print(f"[INFO] No instances found with tag '{key}={value}'")
        return []

def start_instances(instances):
    for instance_id, state in instances:
        if state == 'stopped':
            try:
                print(f"[ACTION] Starting instance {instance_id}")
                ec2.Instance(instance_id).start()
            except Exception as e:
                print(f"[ERROR] Failed to start instance {instance_id}: {e}")
        else:
            print(f"[SKIP] Instance {instance_id} is in '{state}' state")

def stop_instances(instances):
    for instance_id, state in instances:
        if state == 'running':
            try:
                print(f"[ACTION] Stopping instance {instance_id}")
                ec2.Instance(instance_id).stop()
            except Exception as e:
                print(f"[ERROR] Failed to stop instance {instance_id}: {e}")
        else:
            print(f"[SKIP] Instance {instance_id} is in '{state}' state")

def lambda_handler(event, context):
    # Current time in IST
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    current_time = now.strftime('%H:%M')
    print(f"[TIME] Current IST time: {current_time}")

    # Define custom start time blocks
    start_tag_times = {
        'ST-10:00': ('10:00', '10:05'),
        'ST-10:05': ('10:05', '10:10'),
        'ST-10:10': ('10:10', '10:15'),
        'ST-10:15': ('10:15', '10:20'),
        'ST-10:20': ('10:20', '10:25'),
        'ST-10:25': ('10:25', '10:30'),
        'ST-10:30': ('10:30', '10:35'),
        'ST-10:35': ('10:35', '10:40'),
        
        # Add more as needed
    }

    # Define custom stop time blocks
    stop_tag_times = {
        'SD-22:00': ('22:00', '22:05'),
        'SD-22:05': ('22:05', '22:10'),
        'SD-22:10': ('22:10', '22:15'),
        'SD-22:15': ('22:15', '22:20'),
        'SD-22:20': ('22:20', '22:25'),
        'SD-22:25': ('22:25', '22:30'),
        'SD-22:30': ('22:30', '22:35'),
        'SD-22:35': ('22:35', '22:40'),
        
        # Add more as needed
    }

    # Start logic
    for tag_value, (start_time, end_time) in start_tag_times.items():
        if start_time <= current_time <= end_time:
            print(f"[MATCH] Time matched for Start Tag: {tag_value}")
            instances = print_instances_by_tag(start_tag_key, tag_value)
            start_instances(instances)

    # Stop logic
    for tag_value, (start_time, end_time) in stop_tag_times.items():
        if start_time <= current_time <= end_time:
            print(f"[MATCH] Time matched for Stop Tag: {tag_value}")
            instances = print_instances_by_tag(stop_tag_key, tag_value)
            stop_instances(instances)

    return {
        'statusCode': 200,
        'body': 'Custom EC2 scheduler executed.'
    }