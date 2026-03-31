# Lambda — Hello World via AWS CLI

A minimal Lambda to understand the lifecycle: create role → deploy → invoke → see logs → delete.

## What happens when Lambda runs

```
You invoke Lambda
      ↓
AWS spins up a container (cold start ~1s)
      ↓
Runs your handler.py
      ↓
Returns response
      ↓
Container stays warm for ~15min (reused on next call)
      ↓
Idle too long → container destroyed → next call is cold again
```

## Prerequisites

```bash
aws configure        # needs AWS credentials
```

## Step 1 — Create IAM Role

Lambda needs permission to run and write logs.

```bash
# Create the role
aws iam create-role \
  --role-name lambda-basic-role \
  --assume-role-policy-document file://trust-policy.json

# Attach basic execution policy (allows writing CloudWatch logs)
aws iam attach-role-policy \
  --role-name lambda-basic-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## Step 2 — Package the Code

Lambda expects a zip file.

```bash
zip function.zip handler.py
```

## Step 3 — Deploy

Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

```bash
# Get your account ID
aws sts get-caller-identity --query Account --output text

# Create function
aws lambda create-function \
  --function-name hello-lambda \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-basic-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip
```

## Step 4 — Invoke

```bash
# Invoke with a payload
aws lambda invoke \
  --function-name hello-lambda \
  --payload '{"name": "Hoa"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# See the response
cat response.json
# {"message": "Hello, Hoa!"}
```

## Step 5 — See Logs

```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/hello-lambda \
  --order-by LastEventTime \
  --descending \
  --max-items 1

# Read latest log stream (replace LOG_STREAM_NAME)
aws logs get-log-events \
  --log-group-name /aws/lambda/hello-lambda \
  --log-stream-name "LOG_STREAM_NAME"
```

## Step 6 — Update Code (no redeploy, just re-zip)

```bash
zip function.zip handler.py

aws lambda update-function-code \
  --function-name hello-lambda \
  --zip-file fileb://function.zip
```

## Step 7 — Invoke via AWS REST API (no CLI)

The AWS CLI is just a wrapper. Under the hood it calls this HTTP endpoint:

```
POST https://lambda.{region}.amazonaws.com/2015-03-31/functions/{function-name}/invocations
```

The problem: every AWS API call must be signed with **AWS Signature Version 4**. This is why plain `curl` doesn't work directly.

### Option A — curl with awscurl (easiest)

```bash
pip install awscurl

awscurl \
  --service lambda \
  --region ap-southeast-1 \
  -X POST \
  -d '{"name": "Hoa"}' \
  https://lambda.ap-southeast-1.amazonaws.com/2015-03-31/functions/hello-lambda/invocations
```

`awscurl` reads your `~/.aws/credentials` and signs the request automatically.

### Option B — Python with boto3 (programmatic)

```python
import boto3
import json

client = boto3.client("lambda", region_name="ap-southeast-1")

response = client.invoke(
    FunctionName="hello-lambda",
    Payload=json.dumps({"name": "Hoa"})
)

result = json.loads(response["Payload"].read())
print(result)
# {'statusCode': 200, 'body': '{"message": "Hello, Hoa!"}'}
```

boto3 handles SigV4 signing for you — same as AWS CLI.

### Option C — API Gateway in front (plain HTTP, no signing)

This is the real-world pattern. Put API Gateway in front of Lambda so anyone can call it with plain curl.

```bash
# Create HTTP API Gateway and connect to Lambda
aws apigatewayv2 create-api \
  --name hello-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:ap-southeast-1:YOUR_ACCOUNT_ID:function:hello-lambda

# Give API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name hello-lambda \
  --statement-id api-gateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com
```

API Gateway returns a public URL:
```
https://{api-id}.execute-api.ap-southeast-1.amazonaws.com/
```

Now plain curl works — no signing needed:
```bash
curl -X POST https://{api-id}.execute-api.ap-southeast-1.amazonaws.com/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Hoa"}'

# {"message": "Hello, Hoa!"}
```

### Why the difference?

```
Direct Lambda API   →  internal, requires SigV4, caller must be AWS identity
API Gateway         →  public HTTP, API Gateway authenticates for you
```

```
Internet user
      ↓
  API Gateway       ← handles auth, rate limiting, routing
      ↓
   Lambda           ← only sees clean HTTP event, no AWS signing
```

---

## Step 8 — Clean Up (avoid charges)

```bash
# Delete function
aws lambda delete-function --function-name hello-lambda

# Detach policy and delete role
aws iam detach-role-policy \
  --role-name lambda-basic-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name lambda-basic-role
```

## What You Just Saw

| Step | Concept |
|------|---------|
| IAM Role | Lambda needs identity to access AWS resources |
| zip + deploy | Lambda runs your code inside AWS-managed container |
| invoke | Pay-per-call, no server running between calls |
| CloudWatch logs | stdout automatically captured — 12-Factor in action |
| update-function-code | Redeploy = new zip, no server to SSH into |

## Key Observation

You never:
- provisioned a server
- configured nginx
- managed a process

AWS operated it. You only wrote `handler.py`.
