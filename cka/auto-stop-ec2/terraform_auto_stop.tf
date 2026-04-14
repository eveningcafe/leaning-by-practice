terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_ec2_stop_role" {
  name = "lambda-ec2-auto-stop-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda to stop EC2 instances, manage volumes, and EKS nodegroups
resource "aws_iam_role_policy" "lambda_ec2_stop_policy" {
  name = "lambda-ec2-stop-policy"
  role = aws_iam_role.lambda_ec2_stop_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:StopInstances",
          "ec2:DescribeTags",
          "ec2:DescribeVolumes",
          "ec2:DeleteVolume",
          "ec2:CreateSnapshot",
          "ec2:CreateTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "eks:ListClusters",
          "eks:DescribeCluster",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup",
          "eks:DeleteNodegroup",
          "eks:DeleteCluster"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudtrail:LookupEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_auto_stop.py"
  output_path = "lambda_auto_stop.zip"
}

# Lambda Function
resource "aws_lambda_function" "ec2_auto_stop" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "ec2-auto-stop"
  role            = aws_iam_role.lambda_ec2_stop_role.arn
  handler         = "lambda_auto_stop.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      TARGET_REGION = "ap-southeast-1"
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/ec2-auto-stop"
  retention_in_days = 7
}

# EventBridge Rule - Stop instances every day at 12 AM SGT (4 PM UTC previous day)
resource "aws_cloudwatch_event_rule" "daily_stop_midnight" {
  name                = "ec2-daily-stop-midnight"
  description         = "Stop EC2 instances daily at 12 AM SGT (midnight)"
  schedule_expression = "cron(0 16 * * ? *)"  # 12 AM SGT = 4 PM UTC (previous day)
}

# EventBridge Rule - Stop instances after 8 hours of running (every hour check)
resource "aws_cloudwatch_event_rule" "hourly_check_8hours" {
  name                = "ec2-hourly-check-8hours"
  description         = "Check and stop instances running longer than 8 hours"
  schedule_expression = "rate(1 hour)"
}


# Lambda permission for EventBridge - Daily stop
resource "aws_lambda_permission" "allow_eventbridge_daily" {
  statement_id  = "AllowExecutionFromEventBridgeDaily"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_auto_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_stop_midnight.arn
}

# Lambda permission for EventBridge - Hourly check
resource "aws_lambda_permission" "allow_eventbridge_hourly" {
  statement_id  = "AllowExecutionFromEventBridgeHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_auto_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_check_8hours.arn
}


# EventBridge Target - Daily stop (stop all with AutoStop tag)
resource "aws_cloudwatch_event_target" "daily_lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_stop_midnight.name
  target_id = "LambdaTarget"
  arn       = aws_lambda_function.ec2_auto_stop.arn

  input = jsonencode({
    stop_by_tag = true
  })
}

# EventBridge Target - Hourly check (stop instances running > 8 hours)
resource "aws_cloudwatch_event_target" "hourly_lambda_target" {
  rule      = aws_cloudwatch_event_rule.hourly_check_8hours.name
  target_id = "LambdaTarget"
  arn       = aws_lambda_function.ec2_auto_stop.arn

  input = jsonencode({
    max_running_hours = 8
  })
}


# Lambda function for cleaning volumes
data "archive_file" "lambda_clean_volumes_zip" {
  type        = "zip"
  source_file = "lambda_clean_volumes.py"
  output_path = "lambda_clean_volumes.zip"
}

resource "aws_lambda_function" "ebs_auto_clean" {
  filename         = data.archive_file.lambda_clean_volumes_zip.output_path
  function_name    = "ebs-auto-clean"
  role            = aws_iam_role.lambda_ec2_stop_role.arn
  handler         = "lambda_clean_volumes.lambda_handler"
  source_code_hash = data.archive_file.lambda_clean_volumes_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      TARGET_REGION = "ap-southeast-1"
    }
  }
}

# CloudWatch Log Group for volume cleaning
resource "aws_cloudwatch_log_group" "volume_clean_logs" {
  name              = "/aws/lambda/ebs-auto-clean"
  retention_in_days = 7
}

# EventBridge Rule - Clean unattached volumes daily
resource "aws_cloudwatch_event_rule" "daily_volume_clean" {
  name                = "ebs-daily-clean"
  description         = "Clean unattached EBS volumes daily"
  schedule_expression = "cron(0 17 * * ? *)"  # Daily at 1 AM SGT
}

# Lambda permission for EventBridge - Volume cleaning
resource "aws_lambda_permission" "allow_eventbridge_volume_clean" {
  statement_id  = "AllowExecutionFromEventBridgeVolumeClean"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ebs_auto_clean.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_volume_clean.arn
}

# EventBridge Target - Daily volume clean
resource "aws_cloudwatch_event_target" "daily_volume_clean_target" {
  rule      = aws_cloudwatch_event_rule.daily_volume_clean.name
  target_id = "LambdaTarget"
  arn       = aws_lambda_function.ebs_auto_clean.arn

  input = jsonencode({
    days_unattached = 7,
    dry_run = false,
    exclude_tagged = true,
    create_snapshot_before_delete = false
  })
}

# Output
output "lambda_function_name" {
  value = aws_lambda_function.ec2_auto_stop.function_name
}

output "lambda_volume_clean_name" {
  value = aws_lambda_function.ebs_auto_clean.function_name
}

output "daily_rule_name" {
  value = aws_cloudwatch_event_rule.daily_stop_midnight.name
}

output "hourly_rule_name" {
  value = aws_cloudwatch_event_rule.hourly_check_8hours.name
}

# Lambda function for EKS nodegroup cleanup
data "archive_file" "lambda_eks_zip" {
  type        = "zip"
  source_file = "lambda_eks_auto_delete.py"
  output_path = "lambda_eks_auto_delete.zip"
}

resource "aws_lambda_function" "eks_auto_delete" {
  filename         = data.archive_file.lambda_eks_zip.output_path
  function_name    = "eks-nodegroup-auto-delete"
  role            = aws_iam_role.lambda_ec2_stop_role.arn
  handler         = "lambda_eks_auto_delete.lambda_handler"
  source_code_hash = data.archive_file.lambda_eks_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      TARGET_REGION = "ap-southeast-1"
    }
  }
}

# CloudWatch Log Group for EKS cleanup
resource "aws_cloudwatch_log_group" "eks_cleanup_logs" {
  name              = "/aws/lambda/eks-nodegroup-auto-delete"
  retention_in_days = 7
}

# EventBridge Rule - Check EKS nodegroups every 30 minutes
resource "aws_cloudwatch_event_rule" "eks_nodegroup_check" {
  name                = "eks-nodegroup-check-30min"
  description         = "Check and delete EKS nodegroups running >3 hours"
  schedule_expression = "rate(30 minutes)"
}

# Lambda permission for EventBridge - EKS cleanup
resource "aws_lambda_permission" "allow_eventbridge_eks" {
  statement_id  = "AllowExecutionFromEventBridgeEKS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.eks_auto_delete.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.eks_nodegroup_check.arn
}

# EventBridge Target - EKS nodegroup check
resource "aws_cloudwatch_event_target" "eks_nodegroup_target" {
  rule      = aws_cloudwatch_event_rule.eks_nodegroup_check.name
  target_id = "LambdaTarget"
  arn       = aws_lambda_function.eks_auto_delete.arn

  input = jsonencode({
    max_hours = 3,
    dry_run = false,
    exclude_tagged = true
  })
}

output "daily_volume_clean_rule" {
  value = aws_cloudwatch_event_rule.daily_volume_clean.name
}

output "eks_nodegroup_check_rule" {
  value = aws_cloudwatch_event_rule.eks_nodegroup_check.name
}

# Lambda function for idle EKS cluster cleanup
data "archive_file" "lambda_eks_idle_zip" {
  type        = "zip"
  source_file = "lambda_eks_idle_cluster_delete.py"
  output_path = "lambda_eks_idle_cluster_delete.zip"
}

resource "aws_lambda_function" "eks_idle_delete" {
  filename         = data.archive_file.lambda_eks_idle_zip.output_path
  function_name    = "eks-idle-cluster-delete"
  role            = aws_iam_role.lambda_ec2_stop_role.arn
  handler         = "lambda_eks_idle_cluster_delete.lambda_handler"
  source_code_hash = data.archive_file.lambda_eks_idle_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for CloudTrail lookups

  environment {
    variables = {
      TARGET_REGION = "ap-southeast-1"
    }
  }
}

# CloudWatch Log Group for idle EKS cleanup
resource "aws_cloudwatch_log_group" "eks_idle_logs" {
  name              = "/aws/lambda/eks-idle-cluster-delete"
  retention_in_days = 7
}

# EventBridge Rule - Check idle EKS clusters daily
resource "aws_cloudwatch_event_rule" "eks_idle_check" {
  name                = "eks-idle-cluster-daily-check"
  description         = "Check and delete EKS clusters with no activity for 3 days"
  schedule_expression = "cron(0 18 * * ? *)"  # Daily at 2 AM SGT
}

# Lambda permission for EventBridge - Idle EKS cleanup
resource "aws_lambda_permission" "allow_eventbridge_eks_idle" {
  statement_id  = "AllowExecutionFromEventBridgeEKSIdle"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.eks_idle_delete.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.eks_idle_check.arn
}

# EventBridge Target - Idle EKS cluster check
resource "aws_cloudwatch_event_target" "eks_idle_target" {
  rule      = aws_cloudwatch_event_rule.eks_idle_check.name
  target_id = "LambdaTarget"
  arn       = aws_lambda_function.eks_idle_delete.arn

  input = jsonencode({
    idle_days = 3,
    dry_run = false,
    exclude_tagged = true
  })
}

output "lambda_eks_delete_name" {
  value = aws_lambda_function.eks_auto_delete.function_name
}

output "lambda_eks_idle_delete_name" {
  value = aws_lambda_function.eks_idle_delete.function_name
}

output "eks_idle_check_rule" {
  value = aws_cloudwatch_event_rule.eks_idle_check.name
}