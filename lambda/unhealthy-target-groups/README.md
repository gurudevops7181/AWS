# AWS Lambda: Unhealthy Target Group Monitor 🚨

This AWS Lambda function monitors **unhealthy EC2 instances** in **Application Load Balancer (ALB) Target Groups** based on **CloudWatch alarms** and sends notifications through **Amazon SNS**.

---

## 📋 **Overview**

This script performs the following tasks:

- Listens to **CloudWatch Alarm** notifications via **SNS**.
- Checks the **Target Group health** using the **ELBv2 API**.
- Verifies the **alarm state** (`OK` or `ALARM`).
- Retrieves **private IPs** of unhealthy EC2 instances.
- Publishes a detailed **SNS alert message** for any new unhealthy instances detected.

---

## ⚙️ **AWS Services Used**

- **AWS Lambda** — To run the script automatically on SNS trigger.  
- **Amazon CloudWatch** — To monitor target group health metrics.  
- **Elastic Load Balancer (ALB)** — Source of Target Groups and instance health.  
- **Amazon SNS** — For sending alert notifications.  
- **Amazon EC2** — To fetch instance details such as private IP.

---

## 🧩 **Environment Setup**


### 1️⃣ Clone this repository
```bash
git clone git@github.com:gurudevops7181/AWS.git
cd AWS





2️⃣ Install dependencies (for local testing)

pip install boto3


Inside the lambda_handler() function, update:

target_group_arns = {
    'cloudwatch alarm-name': "Target-group-arn",  # Replace with actual values
}
sns_topic_arn = "SNS-TOPIC-NAME"  # Replace with your SNS topic ARN




🧠 How It Works
	1.	Lambda is triggered by an SNS topic subscribed to CloudWatch alarms.
	2.	The function extracts the AlarmName and matches it with the Target Group ARN.
	3.	It calls describe_target_health() to find unhealthy instances.
	4.	If the instance is unhealthy and the alarm state is ALARM, it sends a notification to SNS.
	5.	Duplicate notifications are avoided by tracking previously unhealthy instances within the Lambda context.


New unhealthy instances detected with Alarm State ALARM:
Target Group: arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/my-tg/abcd1234
ID: i-0123456789abcdef0
Private IP: 10.0.2.45
Alarm State: ALARM
Timestamp: 2025-10-22T11:45:31.123Z



🧰 IAM Permissions Required
{
  "Effect": "Allow",
  "Action": [
    "ec2:DescribeInstances",
    "cloudwatch:DescribeAlarms",
    "elasticloadbalancing:DescribeTargetHealth",
    "sns:Publish"
  ],
  "Resource": "*"
}


🧑‍💻 Author
Gurunadh Chippada
DevOps Engineer | AWS | Automation | Docker | Terraform | K8s | ansible | Gitlab
📧 gurujames7181@gmail.com
🌐 https://www.linkedin.com/in/chippada-gurunadh-2b71271b4/