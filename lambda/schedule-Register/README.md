📋 Features

✅ Reads a configuration file containing Target Group ARNs, EC2 instance IDs, and scheduled times.
✅ Automatically determines whether the target group type is instance or IP.
✅ Deregisters instances from target groups within a defined time window (in IST).
✅ Uses boto3 to interact with AWS ELBv2 and EC2 APIs.
✅ Designed for AWS Lambda, but can also be run locally for testing.



🏗️ Architecture Overview

+-------------------+
| target_instances.txt |
+-------------------+
          ↓
+-------------------+
| AWS Lambda Function |
|  - Reads file        |
|  - Checks time slot  |
|  - Calls boto3 APIs  |
+-------------------+
          ↓
+------------------------+
| AWS ELB Target Groups  |
|  Deregister instances  |
+------------------------+



⚙️ File Format
[target-group-arn][i-0123456789abcd,i-0987654321abcd][10:50]
[target-group-arn][i-0abc123def456ghi][10:50]


🕒 Time Window

The script checks if the current IST time falls within the configured range.
You can customize time slots inside this section of the code:
start_tag_times = {
    '10:50': ('10:50', '11:00'),
    # Add more time slots if needed
}

You can define multiple ranges like:

start_tag_times = {
    '10:50': ('10:50', '11:00'),
    '15:30': ('15:30', '15:45'),
}



🧩 Environment Setup

1️⃣ Prerequisites
	•	Python 3.9+
	•	AWS credentials configured (either via IAM role, environment variables, or ~/.aws/credentials)
	•	boto3 library

2️⃣ Install dependencies
pip install boto3

3️⃣ Run locally for testing
python deregister_targets.py



🧪 Example Output

Current IST time: 10:52
Current time 10:52 is within the range 10:50 - 11:00 for registration.
Targets [{'Id': 'i-0123456789abcd'}] deregistered from target group arn:aws:elasticloadbalancing:ap-south-1:111111111111:targetgroup/test/123abc.



Gurunadh
DevOps Engineer | AWS | Automation | Docker | Terraform | Kubernetes | Ansible | GitLab
📧 gurujames7181@gmail.com
🔗 LinkedIn
💻 GitHub