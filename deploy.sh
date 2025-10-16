#!/bin/bash

# AWS IAM Solution - Deployment Script
# This script automates the deployment of the Terraform-based AWS IAM Solution

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites are met"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    python3 terraform_manager.py init
    print_success "Terraform initialized"
}

# Create Lambda package
create_lambda_package() {
    print_status "Creating Lambda deployment package..."
    python3 terraform_manager.py package-lambda
    print_success "Lambda package created"
}

# Validate Terraform configuration
validate_terraform() {
    print_status "Validating Terraform configuration..."
    python3 terraform_manager.py validate
    print_success "Terraform configuration is valid"
}

# Plan Terraform deployment
plan_terraform() {
    print_status "Creating Terraform plan..."
    python3 terraform_manager.py plan
    print_success "Terraform plan created"
}

# Apply Terraform configuration
apply_terraform() {
    print_status "Applying Terraform configuration..."
    python3 terraform_manager.py apply --auto-approve
    print_success "Terraform configuration applied"
}

# Show outputs
show_outputs() {
    print_status "Retrieving deployment outputs..."
    python3 terraform_manager.py outputs
}

# Main deployment function
deploy() {
    print_status "Starting AWS IAM Solution deployment..."
    
    check_prerequisites
    install_dependencies
    init_terraform
    create_lambda_package
    validate_terraform
    plan_terraform
    
    # Ask for confirmation before applying
    echo
    print_warning "This will create AWS resources in your account."
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apply_terraform
        show_outputs
        print_success "AWS IAM Solution deployed successfully!"
    else
        print_warning "Deployment cancelled by user"
        exit 0
    fi
}

# Destroy function
destroy() {
    print_warning "This will destroy all AWS resources created by this Terraform configuration."
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Destroying AWS resources..."
        python3 terraform_manager.py destroy --auto-approve
        print_success "AWS resources destroyed"
    else
        print_warning "Destruction cancelled by user"
    fi
}

# Show help
show_help() {
    echo "AWS IAM Solution - Deployment Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy    Deploy the AWS IAM Solution (default)"
    echo "  destroy   Destroy all AWS resources"
    echo "  plan      Create a Terraform plan without applying"
    echo "  validate  Validate Terraform configuration"
    echo "  outputs   Show Terraform outputs"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0                # Deploy the solution"
    echo "  $0 plan           # Create a plan"
    echo "  $0 destroy        # Destroy resources"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    destroy)
        destroy
        ;;
    plan)
        check_prerequisites
        install_dependencies
        init_terraform
        create_lambda_package
        validate_terraform
        plan_terraform
        ;;
    validate)
        check_prerequisites
        install_dependencies
        init_terraform
        validate_terraform
        ;;
    outputs)
        show_outputs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac