# AWS IAM Solution - Terraform Configuration
# This configuration deploys AWS Organizations, Identity Center, and IAM monitoring

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider for GovCloud
provider "aws" {
  region = var.aws_region
  
  # GovCloud specific configuration
  endpoints {
    organizations    = "https://organizations.us-gov-west-1.amazonaws.com"
    sso             = "https://sso.us-gov-west-1.amazonaws.com"
    accessanalyzer  = "https://access-analyzer.us-gov-west-1.amazonaws.com"
    ssoadmin        = "https://sso.us-gov-west-1.amazonaws.com"
  }
}

# Data source for existing organization (since it already exists)
data "aws_organizations_organization" "existing" {
  provider = aws
}

# Data source for organization root
data "aws_organizations_organizational_units" "root" {
  provider = aws
  parent_id = data.aws_organizations_organization.existing.roots[0].id
}

# Create Security OU
resource "aws_organizations_organizational_unit" "security" {
  provider = aws
  name      = "Security"
  parent_id = data.aws_organizations_organization.existing.roots[0].id

  tags = merge(var.tags, {
    Name = "Security OU"
  })
}

# Create SCP for MFA requirement
resource "aws_organizations_policy" "mfa_policy" {
  provider = aws
  name     = "require-mfa"
  type     = "SERVICE_CONTROL_POLICY"
  
  content = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RequireMFA"
        Effect = "Deny"
        NotAction = [
          "iam:CreateVirtualMFADevice",
          "iam:EnableMFADevice",
          "iam:GetUser",
          "iam:ListMFADevices",
          "iam:ListVirtualMFADevices",
          "iam:ResyncMFADevice"
        ]
        Resource = "*"
        Condition = {
          BoolIfExists = {
            "aws:MultiFactorAuthPresent" = "false"
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "MFA Requirement Policy"
  })
}

# Attach MFA policy to Security OU
resource "aws_organizations_policy_attachment" "mfa_policy_attachment" {
  provider = aws
  policy_id = aws_organizations_policy.mfa_policy.id
  target_id = aws_organizations_organizational_unit.security.id
}

# Data source for existing Identity Center instance
data "aws_ssoadmin_instances" "main" {
  provider = aws
}

# Admin Permission Set
resource "aws_ssoadmin_permission_set" "admin" {
  provider         = aws
  instance_arn     = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  name             = "AdminAccess"
  session_duration = "PT4H"
  description      = "Administrator access permission set"
}

# Attach AdministratorAccess policy to admin permission set
resource "aws_ssoadmin_managed_policy_attachment" "admin_policy" {
  provider           = aws
  instance_arn       = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  permission_set_arn = aws_ssoadmin_permission_set.admin.arn
  managed_policy_arn = "arn:aws-us-gov:iam::aws:policy/AdministratorAccess"
}

# ReadOnly Permission Set
resource "aws_ssoadmin_permission_set" "readonly" {
  provider         = aws
  instance_arn     = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  name             = "ReadOnlyAccess"
  session_duration = "PT4H"
  description      = "Read-only access permission set"
}

# Attach ReadOnlyAccess policy to readonly permission set
resource "aws_ssoadmin_managed_policy_attachment" "readonly_policy" {
  provider           = aws
  instance_arn       = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
  managed_policy_arn = "arn:aws-us-gov:iam::aws:policy/ReadOnlyAccess"
}

# PowerUser Permission Set
resource "aws_ssoadmin_permission_set" "poweruser" {
  provider         = aws
  instance_arn     = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  name             = "PowerUser"
  session_duration = "PT4H"
  description      = "Power user access permission set"
}

# Attach PowerUserAccess policy to poweruser permission set
resource "aws_ssoadmin_managed_policy_attachment" "poweruser_policy" {
  provider           = aws
  instance_arn       = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  permission_set_arn = aws_ssoadmin_permission_set.poweruser.arn
  managed_policy_arn = "arn:aws-us-gov:iam::aws:policy/PowerUserAccess"
}

# IAM Access Analyzer for Organization
resource "aws_accessanalyzer_analyzer" "org_analyzer" {
  provider     = aws
  analyzer_name = "org-analyzer"
  type         = "ORGANIZATION"
  
  tags = merge(var.tags, {
    Name = "Organization Access Analyzer"
  })
}

# Lambda function for automated remediation
resource "aws_lambda_function" "remediation" {
  provider      = aws
  filename      = "lambda_remediation.zip"
  function_name = "iam-remediation-function"
  role          = aws_iam_role.lambda_remediation_role.arn
  handler       = "index.handler"
  runtime       = "python3.9"
  timeout       = 300

  tags = merge(var.tags, {
    Name = "IAM Remediation Function"
  })
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_remediation_role" {
  provider = aws
  name     = "iam-remediation-lambda-role"

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

  tags = merge(var.tags, {
    Name = "IAM Remediation Lambda Role"
  })
}

# Attach basic execution policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  provider   = aws
  role       = aws_iam_role.lambda_remediation_role.name
  policy_arn = "arn:aws-us-gov:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Lambda remediation function
resource "aws_iam_role_policy" "lambda_remediation_policy" {
  provider = aws
  name     = "lambda-remediation-policy"
  role     = aws_iam_role.lambda_remediation_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "access-analyzer:GetAnalyzer",
          "access-analyzer:ListFindings",
          "access-analyzer:GetFinding",
          "access-analyzer:UpdateFindings",
          "iam:GetRole",
          "iam:GetUser",
          "iam:ListAttachedRolePolicies",
          "iam:ListRolePolicies",
          "iam:GetRolePolicy",
          "iam:ListPolicies",
          "iam:GetPolicy",
          "iam:GetPolicyVersion"
        ]
        Resource = "*"
      }
    ]
  })
}

# EventBridge rule for Access Analyzer findings
resource "aws_cloudwatch_event_rule" "access_analyzer_findings" {
  provider    = aws
  name        = "access-analyzer-findings"
  description = "Capture Access Analyzer findings"

  event_pattern = jsonencode({
    source      = ["aws.access-analyzer"]
    detail-type = ["Access Analyzer Finding"]
  })

  tags = merge(var.tags, {
    Name = "Access Analyzer Findings Rule"
  })
}

# EventBridge target for Lambda function
resource "aws_cloudwatch_event_target" "lambda_target" {
  provider  = aws
  rule      = aws_cloudwatch_event_rule.access_analyzer_findings.name
  target_id = "IAMRemediationTarget"
  arn       = aws_lambda_function.remediation.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  provider      = aws
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.access_analyzer_findings.arn
}