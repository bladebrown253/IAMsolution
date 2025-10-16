# Outputs for AWS IAM Solution Terraform Configuration

output "organization_id" {
  description = "The ID of the AWS Organization"
  value       = data.aws_organizations_organization.existing.id
}

output "organization_arn" {
  description = "The ARN of the AWS Organization"
  value       = data.aws_organizations_organization.existing.arn
}

output "organization_root_id" {
  description = "The Root ID of the AWS Organization"
  value       = data.aws_organizations_organization.existing.roots[0].id
}

output "security_ou_id" {
  description = "The ID of the Security Organizational Unit"
  value       = aws_organizations_organizational_unit.security.id
}

output "security_ou_arn" {
  description = "The ARN of the Security Organizational Unit"
  value       = aws_organizations_organizational_unit.security.arn
}

output "mfa_policy_id" {
  description = "The ID of the MFA requirement policy"
  value       = aws_organizations_policy.mfa_policy.id
}

output "mfa_policy_arn" {
  description = "The ARN of the MFA requirement policy"
  value       = aws_organizations_policy.mfa_policy.arn
}

output "identity_center_instance_arn" {
  description = "The ARN of the Identity Center instance"
  value       = aws_ssoadmin_instance.main.arn
}

output "identity_center_instance_id" {
  description = "The ID of the Identity Center instance"
  value       = aws_ssoadmin_instance.main.id
}

output "permission_sets" {
  description = "Map of permission set names to their ARNs"
  value = {
    admin     = aws_ssoadmin_permission_set.admin.arn
    readonly  = aws_ssoadmin_permission_set.readonly.arn
    poweruser = aws_ssoadmin_permission_set.poweruser.arn
  }
}

output "access_analyzer_arn" {
  description = "The ARN of the Access Analyzer"
  value       = aws_accessanalyzer_analyzer.org_analyzer.arn
}

output "access_analyzer_name" {
  description = "The name of the Access Analyzer"
  value       = aws_accessanalyzer_analyzer.org_analyzer.analyzer_name
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda remediation function"
  value       = aws_lambda_function.remediation.arn
}

output "lambda_function_name" {
  description = "The name of the Lambda remediation function"
  value       = aws_lambda_function.remediation.function_name
}

output "lambda_role_arn" {
  description = "The ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_remediation_role.arn
}

output "eventbridge_rule_arn" {
  description = "The ARN of the EventBridge rule for Access Analyzer findings"
  value       = aws_cloudwatch_event_rule.access_analyzer_findings.arn
}

output "eventbridge_rule_name" {
  description = "The name of the EventBridge rule for Access Analyzer findings"
  value       = aws_cloudwatch_event_rule.access_analyzer_findings.name
}