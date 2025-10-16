#!/usr/bin/env python3
"""
Test Deployment Script
This script performs basic tests to ensure the Terraform configuration is ready for deployment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_aws_cli():
    """Test AWS CLI configuration."""
    print("🔍 Testing AWS CLI configuration...")
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            check=True
        )
        identity = json.loads(result.stdout)
        print(f"✅ AWS CLI configured for account: {identity.get('Account')}")
        print(f"   User/Role: {identity.get('Arn')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ AWS CLI not configured: {e}")
        return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False

def test_terraform_available():
    """Test if Terraform is available."""
    print("🔍 Testing Terraform availability...")
    try:
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.split('\n')[0]
        print(f"✅ {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Terraform error: {e}")
        return False
    except FileNotFoundError:
        print("❌ Terraform not installed")
        print("   Install from: https://www.terraform.io/downloads")
        return False

def test_python_dependencies():
    """Test Python dependencies."""
    print("🔍 Testing Python dependencies...")
    try:
        import boto3
        import json
        print("✅ Required Python packages available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def test_configuration_files():
    """Test configuration files exist."""
    print("🔍 Testing configuration files...")
    required_files = [
        "main.tf",
        "variables.tf", 
        "outputs.tf",
        "terraform.tfvars.example",
        "lambda_remediation.py",
        "terraform_manager.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_lambda_package():
    """Test Lambda package creation."""
    print("🔍 Testing Lambda package creation...")
    try:
        # Import the terraform manager
        sys.path.append('.')
        from terraform_manager import TerraformManager
        
        tf_manager = TerraformManager()
        success = tf_manager.create_lambda_package()
        
        if success and Path("lambda_remediation.zip").exists():
            print("✅ Lambda package created successfully")
            return True
        else:
            print("❌ Failed to create Lambda package")
            return False
    except Exception as e:
        print(f"❌ Error creating Lambda package: {e}")
        return False

def test_aws_organization_access():
    """Test access to AWS Organization."""
    print("🔍 Testing AWS Organization access...")
    try:
        result = subprocess.run(
            ["aws", "organizations", "describe-organization"],
            capture_output=True,
            text=True,
            check=True
        )
        org_data = json.loads(result.stdout)
        org_id = org_data.get('Organization', {}).get('Id')
        print(f"✅ Organization access confirmed: {org_id}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Cannot access AWS Organization: {e}")
        print("   Ensure you have organizations:DescribeOrganization permission")
        return False

def test_sso_access():
    """Test access to AWS SSO."""
    print("🔍 Testing AWS SSO access...")
    try:
        result = subprocess.run(
            ["aws", "sso", "list-instances"],
            capture_output=True,
            text=True,
            check=True
        )
        sso_data = json.loads(result.stdout)
        instances = sso_data.get('Instances', [])
        if instances:
            print(f"✅ SSO access confirmed: {len(instances)} instance(s) found")
        else:
            print("⚠️  SSO access confirmed but no instances found")
            print("   You may need to enable SSO in the AWS Console first")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Cannot access AWS SSO: {e}")
        print("   Ensure you have sso:ListInstances permission")
        return False

def main():
    """Run all tests."""
    print("🧪 Running deployment tests...\n")
    
    tests = [
        ("AWS CLI Configuration", test_aws_cli),
        ("Terraform Availability", test_terraform_available),
        ("Python Dependencies", test_python_dependencies),
        ("Configuration Files", test_configuration_files),
        ("Lambda Package Creation", test_lambda_package),
        ("AWS Organization Access", test_aws_organization_access),
        ("AWS SSO Access", test_sso_access),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        print("\nNext steps:")
        print("1. Copy terraform.tfvars.example to terraform.tfvars")
        print("2. Edit terraform.tfvars with your values")
        print("3. Run: ./deploy.sh")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())