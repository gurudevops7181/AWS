🔍 Find ELB Target Group by Private IP

This Python script helps you identify which AWS ELB Target Group a specific private IP address belongs to.
It scans all Target Groups in the selected AWS profile and checks:
	•	Whether the target group type is instance or ip
	•	Matches the provided private IP(s)
	•	Displays ELB Target Group name and instance ID (for instance-type targets)

This tool is helpful for troubleshooting ALB/NLB issues, mapping unknown IPs, or debugging autoscaling targets.

⸻

🚀 Features
	•	Supports multiple private IPs in a single command
	•	Works for both instance-type and ip-type target groups
	•	Uses AWS SDK (boto3)
	•	Fast scanning across all target groups
	•	Read-only — does not modify any AWS resources

⸻

📦 Requirements
	•	Python 3.7+
	•	AWS CLI configured (aws configure)
	•	IAM permissions:
	•	elasticloadbalancing:DescribeTargetGroups
	•	elasticloadbalancing:DescribeTargetHealth
	•	ec2:DescribeInstances

Install Python dependencies:

pip install -r requirements.txt



Run the script using:

python find_target_by_ip.py <aws_profile_name> <private_ip1> [<private_ip2> ...]

Example:

python find_target_by_ip.py prod-profile 10.0.1.15 10.0.5.22

Example Output:

Searching across 16 target groups...

✅ Found match: 10.0.1.15 → TargetGroup: app-prod-web-tg (instance)
   Instance ID: i-0abc123f98cde4567

   📁 File Structure

   .
├── find_target_by_ip.py
├── requirements.txt
└── README.md