# 🕒 AWS Lambda EC2 Scheduler using Tags

This AWS Lambda function automatically **starts** or **stops EC2 instances** based on custom **time-based tags**.  
It uses **boto3** (AWS SDK for Python) and can be scheduled using **Amazon EventBridge** (CloudWatch Events).

---

## 🚀 **Overview**

The function checks EC2 instances for specific tag values like:

- `scheduleStart = ST-10:00`
- `scheduleStop  = SD-22:00`

When the **current time in IST (India Standard Time)** matches the tag value range, the Lambda automatically **starts or stops** the instance accordingly.

---

## ⚙️ **How It Works**

1. Lambda runs every 5 minutes (via **EventBridge schedule rule**).  
2. It reads all EC2 instances with tags:
   - `scheduleStart`
   - `scheduleStop`
3. If the tag’s time range matches the **current IST time**, the instance will:
   - Start (if stopped)
   - Stop (if running)
4. Logs every action and skip in **CloudWatch Logs**.

---

## 🧩 **Tag Structure Example**

| Purpose | Tag Key | Tag Value | Description |
|----------|----------|------------|--------------|
| Start instance | `scheduleStart` | `ST-10:00` | Start between 10:00–10:05 IST |
| Stop instance  | `scheduleStop`  | `SD-22:00` | Stop between 22:00–22:05 IST |

You can define multiple tag values like `ST-10:10`, `ST-10:15`, `SD-22:10`, etc.

---

## 🧰 **AWS Services Used**

- **AWS Lambda** – Executes the Python script on schedule  
- **Amazon EC2** – Instances being started/stopped  
- **Amazon EventBridge (CloudWatch Events)** – Triggers Lambda every 5 minutes  
- **AWS CloudWatch Logs** – Stores execution logs  

---

## 🧑‍💻 **Code Workflow**

```plaintext
Lambda Triggered → Get Current IST Time →
Check EC2 Instances by Tags →
Match Time Slot → Start/Stop Instance →
Log Action to CloudWatch






⚙️ IAM Policy Permissions
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}



🧪 Testing Locally


pip install boto3
python lambda_function.py

Make sure your AWS credentials are configured locally:
aws configure




🕓 EventBridge Schedule Example

To run Lambda every 5 minutes:
	•	Rule name: EC2AutoSchedulerRule
	•	Schedule expression: rate(5 minutes)



🧑‍💻 Author
Gurunadh Chippada
DevOps Engineer | AWS | Automation | Docker | Terraform | K8s | ansible | Gitlab
📧 gurujames7181@gmail.com
🌐 https://www.linkedin.com/in/chippada-gurunadh-2b71271b4/



