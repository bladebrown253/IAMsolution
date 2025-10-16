# Variables for AWS IAM Solution Terraform Configuration

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-gov-west-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "organization_id" {
  description = "Existing AWS Organization ID (o-t73nbfcli)"
  type        = string
  default     = "o-t73nbfcli"
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "AWS IAM Solution"
    ManagedBy   = "Terraform"
    Environment = "prod"
  }
}

variable "mfa_policy_name" {
  description = "Name for the MFA requirement policy"
  type        = string
  default     = "require-mfa"
}

variable "security_ou_name" {
  description = "Name for the Security Organizational Unit"
  type        = string
  default     = "Security"
}

variable "identity_center_name" {
  description = "Name for the Identity Center instance"
  type        = string
  default     = "MainIdentityCenter"
}

variable "permission_sets" {
  description = "Configuration for permission sets"
  type = map(object({
    name             = string
    description      = string
    session_duration = string
    managed_policies = list(string)
  }))
  default = {
    admin = {
      name             = "AdminAccess"
      description      = "Administrator access permission set"
      session_duration = "PT4H"
      managed_policies = ["arn:aws-us-gov:iam::aws:policy/AdministratorAccess"]
    }
    readonly = {
      name             = "ReadOnlyAccess"
      description      = "Read-only access permission set"
      session_duration = "PT4H"
      managed_policies = ["arn:aws-us-gov:iam::aws:policy/ReadOnlyAccess"]
    }
    poweruser = {
      name             = "PowerUser"
      description      = "Power user access permission set"
      session_duration = "PT4H"
      managed_policies = ["arn:aws-us-gov:iam::aws:policy/PowerUserAccess"]
    }
  }
}

variable "lambda_function_name" {
  description = "Name for the Lambda remediation function"
  type        = string
  default     = "iam-remediation-function"
}

variable "lambda_runtime" {
  description = "Python runtime for Lambda function"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 300
}

variable "access_analyzer_name" {
  description = "Name for the Access Analyzer"
  type        = string
  default     = "org-analyzer"
}