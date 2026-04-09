# Fargate - Run Containers Without Managing Servers

## What is Fargate?

**Lambda vs Fargate:**
- Lambda: Run code for max 15 minutes
- Fargate: Run containers forever, any language, any port

**EC2 vs Fargate:**
```
EC2 Container:    You → Manage EC2 → Run Docker → Your App
Fargate:          You → Your App (AWS handles the server)
```

## Prerequisites

```bash
# Make sure AWS CLI is configured and set account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

## Step 1: Build & Push Container

```bash
# 1. Create ECR repository (container registry)
aws ecr create-repository --repository-name my-fargate-app --region ap-southeast-1

# 2. Build Docker image
docker build -t my-fargate-app .

# 3. Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com

# 4. Tag and push
docker tag my-fargate-app:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/my-fargate-app:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/my-fargate-app:latest
```

## Step 2: Create Cluster (FREE - just metadata)

```bash
aws ecs create-cluster --cluster-name my-fargate-cluster
```

## Step 3: Setup IAM Role & Task Definition

```bash
# 1. Create IAM execution role (one time only)
aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-trust-policy.json 2>/dev/null || echo "Role already exists"

aws iam attach-role-policy --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 2. Update task-definition.json with your account ID
sed -i "s/891920435433/$AWS_ACCOUNT_ID/g" task-definition.json

# 3. Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

## Step 4: Run Task (THIS COSTS MONEY ~$0.012/hour)

```bash
# 1. Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/my-app --region ap-southeast-1

# 2. Get VPC subnet and security group
export SUBNET_ID=$(aws ec2 describe-subnets \
  --query 'Subnets[?DefaultForAz==`true`].SubnetId | [0]' \
  --output text --region ap-southeast-1)

export VPC_ID=$(aws ec2 describe-subnets --subnet-ids $SUBNET_ID \
  --query 'Subnets[0].VpcId' --output text --region ap-southeast-1)

export SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[?GroupName==`default`].GroupId | [0]' \
  --output text --region ap-southeast-1)

# 3. Open port 5000 for testing
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID --protocol tcp --port 5000 --cidr 0.0.0.0/0

# 4. Run the task
aws ecs run-task \
  --cluster my-fargate-cluster \
  --task-definition my-app:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"
```

## Step 5: Test Your Container

```bash
# 1. Get task ID
export TASK_ID=$(aws ecs list-tasks --cluster my-fargate-cluster \
  --query 'taskArns[0]' --output text | cut -d'/' -f3)

# 2. Wait for task to be running
aws ecs wait tasks-running --cluster my-fargate-cluster --tasks $TASK_ID

# 3. Get public IP
export ENI_ID=$(aws ecs describe-tasks --cluster my-fargate-cluster --tasks $TASK_ID \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

export PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

# 4. Test the app
echo "Your app is running at: http://$PUBLIC_IP:5000"
curl http://$PUBLIC_IP:5000
curl http://$PUBLIC_IP:5000/health
```

## Step 6: STOP Task (STOP CHARGES!)

```bash
# Stop the task
aws ecs stop-task --cluster my-fargate-cluster --task $TASK_ID

echo "Task stopped - charges stopped!"
```

## Clean Up Everything

```bash
# Delete all resources
aws ecs delete-cluster --cluster my-fargate-cluster
aws ecr delete-repository --repository-name my-fargate-app --force
aws logs delete-log-group --log-group-name /ecs/my-app
aws ec2 revoke-security-group-ingress --group-id $SG_ID --protocol tcp --port 5000 --cidr 0.0.0.0/0

# Keep the IAM role for next time
# aws iam detach-role-policy --role-name ecsTaskExecutionRole \
#   --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
# aws iam delete-role --role-name ecsTaskExecutionRole
```

## Pricing

| Size | vCPU | Memory | Cost/hour | Cost/month (24/7) |
|------|------|--------|-----------|-------------------|
| Tiny | 0.25 | 512 MB | $0.012 | $9 |
| Small | 0.5 | 1 GB | $0.025 | $18 |
| Medium | 1 | 2 GB | $0.05 | $36 |

## Troubleshooting

**Task stays in PENDING:**
- Check CloudWatch logs: `aws logs tail /ecs/my-app`
- Usually means image pull failed - check ECR repository name

**Connection refused:**
- Check security group has port 5000 open
- Check task is RUNNING: `aws ecs describe-tasks --cluster my-fargate-cluster --tasks $TASK_ID`

**AWS CLI errors:**
- Token expired: `aws sso login --profile YOUR_PROFILE`
- Wrong region: Add `--region ap-southeast-1` to commands

## Key Files

- `app.py` - Flask application
- `Dockerfile` - Container definition
- `task-definition.json` - Fargate specs (CPU, memory, image)
- `ecs-trust-policy.json` - IAM permissions

## Key Concepts

- **Task Definition** = Recipe (what image, how much CPU/RAM)
- **Task** = Running container (costs money)
- **Cluster** = Just a name/grouping (free)
- **ECR** = Amazon's Docker Hub

The magic: AWS finds servers, runs your container, bills per second. You never SSH, patch, or manage capacity.