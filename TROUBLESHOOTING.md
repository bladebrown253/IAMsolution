# Troubleshooting Guide

## Common Issues and Solutions

### 1. AWS SSO (Identity Center) Resources

**Issue**: `The provider hashicorp/aws does not support resource type "aws_ssoadmin_instance"`

**Solution**: The `aws_ssoadmin_instance` resource doesn't exist in Terraform. Instead, use data sources to reference existing SSO instances:

```hcl
# Instead of creating an instance, reference existing ones
data "aws_ssoadmin_instances" "main" {
  provider = aws
}

# Use the data source in your resources
resource "aws_ssoadmin_permission_set" "admin" {
  provider         = aws
  instance_arn     = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  name             = "AdminAccess"
  session_duration = "PT4H"
  description      = "Administrator access permission set"
}
```

### 2. GovCloud ARN Issues

**Issue**: Resources fail because of incorrect ARN formats

**Solution**: Ensure all ARNs use the GovCloud format:

```hcl
# Correct GovCloud ARN format
managed_policy_arn = "arn:aws-us-gov:iam::aws:policy/AdministratorAccess"

# Not the commercial format
# managed_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
```

### 3. Provider Configuration Issues

**Issue**: Resources fail to create due to endpoint issues

**Solution**: Ensure proper GovCloud endpoints are configured:

```hcl
provider "aws" {
  region = var.aws_region
  
  endpoints {
    organizations    = "https://organizations.us-gov-west-1.amazonaws.com"
    sso             = "https://sso.us-gov-west-1.amazonaws.com"
    accessanalyzer  = "https://access-analyzer.us-gov-west-1.amazonaws.com"
    ssoadmin        = "https://sso.us-gov-west-1.amazonaws.com"
  }
}
```

### 4. Lambda Function Issues

**Issue**: Lambda function fails to deploy

**Solution**: Ensure the Lambda package is created before applying:

```bash
# Create the Lambda package first
python3 terraform_manager.py package-lambda

# Then apply
python3 terraform_manager.py apply
```

### 5. Organization Access Issues

**Issue**: Cannot create resources in organization

**Solution**: Ensure you have the necessary permissions:

- `organizations:CreateOrganizationalUnit`
- `organizations:CreatePolicy`
- `organizations:AttachPolicy`
- `sso:CreatePermissionSet`
- `sso:AttachManagedPolicyToPermissionSet`
- `access-analyzer:CreateAnalyzer`
- `lambda:CreateFunction`
- `events:PutRule`

### 6. Terraform State Issues

**Issue**: State file conflicts or corruption

**Solution**: 

```bash
# Refresh state
terraform refresh

# If needed, reimport resources
terraform import aws_organizations_organizational_unit.security ou-xxxxx

# Or start fresh (WARNING: This will recreate all resources)
rm terraform.tfstate*
terraform init
terraform apply
```

## Validation Commands

### Check Configuration Syntax
```bash
# Using our custom validator
python3 validate_config.py

# Using Terraform (if installed)
terraform validate
```

### Check Plan Before Apply
```bash
# Always plan first
python3 terraform_manager.py plan

# Review the plan carefully before applying
python3 terraform_manager.py apply
```

### Check Current State
```bash
# List all resources
python3 terraform_manager.py resources

# Show current state
python3 terraform_manager.py state
```

## Debugging Tips

### 1. Enable Debug Logging
```bash
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log
python3 terraform_manager.py apply
```

### 2. Check AWS CLI Configuration
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check current region
aws configure get region

# List available regions
aws ec2 describe-regions --region us-gov-west-1
```

### 3. Verify Organization Access
```bash
# Check organization details
aws organizations describe-organization

# List organizational units
aws organizations list-organizational-units-for-parent --parent-id r-xxxxx
```

### 4. Check SSO Status
```bash
# List SSO instances
aws sso list-instances

# List permission sets (if SSO is configured)
aws ssoadmin list-permission-sets --instance-arn arn:aws-us-gov:sso::account:instance/ssoins-xxxxx
```

## Common Error Messages

### "Access Denied"
- Check IAM permissions
- Verify AWS credentials
- Ensure you're using the correct AWS profile

### "Resource already exists"
- Check if resource was created outside Terraform
- Use `terraform import` to bring it under management
- Or remove the resource from configuration

### "Invalid ARN format"
- Ensure all ARNs use `arn:aws-us-gov:` prefix
- Check resource names and regions

### "Provider not found"
- Run `terraform init` to download providers
- Check provider version constraints

## Getting Help

1. **Check Logs**: Look at Terraform logs and AWS CloudTrail
2. **Validate Configuration**: Use `python3 validate_config.py`
3. **Test Incrementally**: Apply resources one by one
4. **Check Documentation**: Refer to Terraform AWS provider docs
5. **Community Support**: Check Terraform and AWS forums

## Emergency Recovery

If you need to quickly remove all resources:

```bash
# WARNING: This will destroy all resources
python3 terraform_manager.py destroy --auto-approve
```

If Terraform state is corrupted:

```bash
# Remove state and start fresh
rm -rf .terraform/
rm terraform.tfstate*
terraform init
terraform apply
```