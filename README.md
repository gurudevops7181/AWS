# AWS Lambda Automation Suite

This repository contains multiple AWS Lambda scripts to automate EC2 instance scheduling, load balancer target management, and health checks.  
Each module is independent and includes its own README for setup and usage.

---

## 📂 Modules Overview

| Module | Description | Link |
|--------|--------------|------|
| **Schedule-start-stop-ec2** | Automates scheduled start and stop of EC2 instances. | [View Details](https://github.com/gurudevops7181/AWS/blob/main/lambda/Schedule-start-stop-ec2/%F0%9F%A7%A0%20README.md |
| **schedule-Deregister** | Deregisters EC2 instances from target groups for maintenance or scaling down. | [View Details](./schedule-Deregister/README.md) |
| **schedule-Register** | Registers EC2 instances back into target groups after maintenance or scaling up. | [View Details](./schedule-Register/README.md) |
| **unhealthy-target-groups** | Monitors target groups and removes unhealthy targets automatically. | [View Details](./unhealthy-target-groups/README.md) |

---

## 🧩 Features
- Automated EC2 lifecycle control  
- Target group registration/deregistration  
- Unhealthy target detection and handling  
- Modular Lambda function structure  

---

## ⚙️ Usage
Each module can be deployed as an independent AWS Lambda function.  
Refer to the module-specific documentation for detailed setup instructions.

Example:
```bash
cd lambda/Schedule-start-stop-ec2
cat README.md