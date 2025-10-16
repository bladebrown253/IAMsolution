# AWS IAM Solution - Terraform with Python

This project has been migrated from AWS CDK to Terraform with Python automation scripts. It provides a comprehensive AWS IAM solution including Organizations, Identity Center (SSO), and automated monitoring.

## 🏗️ Architecture

The solution deploys the following AWS resources:

- **AWS Organizations**: Security OU and Service Control Policies (SCPs)
- **Identity Center (SSO)**: Permission sets for Admin, ReadOnly, and PowerUser access
- **IAM Monitoring**: Access Analyzer with automated remediation via Lambda
- **EventBridge**: Automated processing of Access Analyzer findings

## 📋 Prerequisites

- Terraform >= 1.0
- Python 3.9+
- AWS CLI configured for GovCloud
- Access to existing AWS Organization (ID: o-t73nbfcli)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd /workspace

# Install Python dependencies
pip install -r requirements.txt

# Make the Terraform manager executable
chmod +x terraform_manager.py
```

### 2. Configure Variables

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit the variables file with your specific values
nano terraform.tfvars
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
python terraform_manager.py init

# Create Lambda package
python terraform_manager.py package-lambda

# Plan the deployment
python terraform_manager.py plan

# Apply the configuration
python terraform_manager.py apply --auto-approve
```

## 🛠️ Management Commands

The `terraform_manager.py` script provides convenient commands for managing your infrastructure:

### Basic Operations

```bash
# Initialize Terraform
python terraform_manager.py init

# Validate configuration
python terraform_manager.py validate

# Create execution plan
python terraform_manager.py plan

# Apply changes
python terraform_manager.py apply

# Destroy resources
python terraform_manager.py destroy
```

### Information Commands

```bash
# Show all outputs
python terraform_manager.py outputs

# List all resources
python terraform_manager.py resources

# Show current state
python terraform_manager.py state
```

### Lambda Management

```bash
# Create Lambda deployment package
python terraform_manager.py package-lambda
```

## 📁 Project Structure

```
/workspace/
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── terraform.tfvars.example  # Example variables file
├── terraform_manager.py       # Python management script
├── lambda_remediation.py      # Lambda function source
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region for resources | `us-gov-west-1` |
| `environment` | Environment name | `prod` |
| `organization_id` | Existing AWS Organization ID | `o-t73nbfcli` |
| `mfa_policy_name` | Name for MFA requirement policy | `require-mfa` |
| `security_ou_name` | Name for Security OU | `Security` |

### Permission Sets

The solution creates three default permission sets:

- **AdminAccess**: Full administrator access
- **ReadOnlyAccess**: Read-only access to all resources
- **PowerUser**: Power user access (no IAM management)

## 🔍 Monitoring and Remediation

### Access Analyzer

The solution includes an Access Analyzer that monitors your organization for:

- Overly permissive IAM policies
- Public S3 buckets
- Unused IAM credentials
- KMS key issues

### Automated Remediation

The Lambda function (`lambda_remediation.py`) automatically processes Access Analyzer findings and provides:

- Risk assessment (HIGH, MEDIUM, LOW)
- Specific remediation recommendations
- Resource-specific guidance

## 🔐 Security Features

### Service Control Policies (SCPs)

- **MFA Requirement**: Enforces MFA for all API calls except MFA management operations
- Applied to the Security OU

### Identity Center Integration

- Centralized access management
- Configurable session durations
- AWS managed policy attachments

## 🚨 Troubleshooting

### Common Issues

1. **Terraform not found**
   ```bash
   # Install Terraform
   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
   sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
   sudo apt-get update && sudo apt-get install terraform
   ```

2. **AWS credentials not configured**
   ```bash
   # Configure AWS CLI for GovCloud
   aws configure --profile govcloud
   export AWS_PROFILE=govcloud
   ```

3. **Lambda package creation fails**
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt
   python terraform_manager.py package-lambda
   ```

### Logs and Debugging

```bash
# Enable verbose logging
export TF_LOG=DEBUG
python terraform_manager.py apply

# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/iam-remediation
```

## 📊 Outputs

After successful deployment, you can retrieve important information:

```bash
# Get all outputs
python terraform_manager.py outputs

# Key outputs include:
# - organization_id: AWS Organization ID
# - identity_center_instance_arn: SSO instance ARN
# - permission_sets: Map of permission set ARNs
# - access_analyzer_arn: Access Analyzer ARN
# - lambda_function_arn: Remediation function ARN
```

## 🔄 Migration from CDK

This project was migrated from AWS CDK. Key changes:

- **Infrastructure as Code**: CDK constructs → Terraform resources
- **Language**: TypeScript/Python CDK → HCL + Python automation
- **State Management**: CDK synthesis → Terraform state
- **Deployment**: `cdk deploy` → `terraform apply`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review Terraform logs
3. Check AWS CloudTrail for API errors
4. Open an issue in the repository

## 🔗 Related Documentation

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Organizations User Guide](https://docs.aws.amazon.com/organizations/)
- [AWS Identity Center User Guide](https://docs.aws.amazon.com/singlesignon/)
- [AWS Access Analyzer User Guide](https://docs.aws.amazon.com/access-analyzer/)