# Auto-Stop EC2 Instances Setup

## Overview
Automatically stop EC2 instances to save costs using AWS Lambda and EventBridge.

## Features
- **Daily Stop**: Stop instances at 12 AM SGT (midnight)
- **Long-Running Stop**: Stop instances running > 8 hours
- **Tag-Based Control**: Use tags to control auto-stop behavior

## Deployment

### Using Terraform
```bash
cd auto-stop-ec2
terraform init
terraform plan
terraform apply
```

### Manual Setup via AWS CLI
```bash
# Create IAM role
aws iam create-role --role-name lambda-ec2-stop \
  --assume-role-policy-document file://trust-policy.json

# Attach policy
aws iam put-role-policy --role-name lambda-ec2-stop \
  --policy-name ec2-stop-policy \
  --policy-document file://policy.json

# Create Lambda function
zip lambda_auto_stop.zip lambda_auto_stop.py
aws lambda create-function \
  --function-name ec2-auto-stop \
  --runtime python3.11 \
  --role arn:aws:iam::891920435433:role/lambda-ec2-stop \
  --handler lambda_auto_stop.lambda_handler \
  --zip-file fileb://lambda_auto_stop.zip \
  --region ap-southeast-1

# Create EventBridge rule
aws events put-rule \
  --name ec2-daily-stop \
  --schedule-expression "cron(0 16 * * ? *)" \
  --region ap-southeast-1
```

## Tag Your Instances

### Method 1: Auto-Stop Tag
```bash
# Add AutoStop tag to enable auto-stopping
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=AutoStop,Value=true \
  --region ap-southeast-1
```

### Method 2: Keep Running Tag
```bash
# Add KeepRunning tag to prevent auto-stopping
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=KeepRunning,Value=true \
  --region ap-southeast-1
```

## Schedule Options

### 1. Daily Schedule (12 AM SGT / Midnight)
```python
# EventBridge input
{
  "stop_by_tag": true
}
```

### 2. Long-Running Instances (Every Hour Check)
```python
# EventBridge input
{
  "max_running_hours": 8
}
```

## Testing

### Test Lambda Function
```bash
# Test with tag-based stopping
aws lambda invoke \
  --function-name ec2-auto-stop \
  --payload '{"stop_by_tag": true}' \
  --region ap-southeast-1 \
  response.json

# Test with max running hours
aws lambda invoke \
  --function-name ec2-auto-stop \
  --payload '{"max_running_hours": 8}' \
  --region ap-southeast-1 \
  response.json
```

## Monitoring

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/ec2-auto-stop --follow --region ap-southeast-1
```

### Check EventBridge Rules
```bash
aws events list-rules --region ap-southeast-1
```

## Cost Savings

For your setup with ~26 running instances:
- **Without auto-stop**: ~$1,000-1,500/month
- **With auto-stop (8hr/day)**: ~$300-500/month
- **Estimated savings**: ~$700-1,000/month (66% reduction)

## Best Practices

1. **Tag all instances** appropriately:
   - Production: `KeepRunning=true`
   - Development: `AutoStop=true`
   - Student VMs: Use naming convention `2601-DE*`

2. **Set appropriate schedules**:
   - Daily: Stop at 12 AM (midnight), start manually when needed
   - Long-running: Auto-stop after 8 hours
   - Holidays: Create special rules

3. **Monitor and adjust**:
   - Review CloudWatch logs weekly
   - Adjust schedules based on usage patterns
   - Add exceptions for special projects

## Troubleshooting

### Instances not stopping
1. Check IAM permissions
2. Verify tags are correct
3. Check Lambda function logs
4. Verify EventBridge rules are enabled

### To disable auto-stop temporarily
```bash
aws events disable-rule --name ec2-daily-stop --region ap-southeast-1
```

### To re-enable
```bash
aws events enable-rule --name ec2-daily-stop --region ap-southeast-1
```