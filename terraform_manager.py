#!/usr/bin/env python3
"""
Terraform Manager for AWS IAM Solution
This script provides Python-based management of the Terraform infrastructure.
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import zipfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TerraformManager:
    """Manages Terraform operations for the AWS IAM Solution."""
    
    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir).resolve()
        self.terraform_dir = self.working_dir
        self.lambda_source = self.working_dir / "lambda_remediation.py"
        self.lambda_zip = self.working_dir / "lambda_remediation.zip"
        
    def run_terraform_command(self, command: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a terraform command and return the result."""
        try:
            logger.info(f"Running: terraform {' '.join(command)}")
            result = subprocess.run(
                ["terraform"] + command,
                cwd=self.terraform_dir,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform command failed: {e}")
            if e.stdout:
                logger.error(f"STDOUT: {e.stdout}")
            if e.stderr:
                logger.error(f"STDERR: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("Terraform not found. Please install Terraform.")
            raise
    
    def init_terraform(self) -> bool:
        """Initialize Terraform working directory."""
        try:
            logger.info("Initializing Terraform...")
            self.run_terraform_command(["init"])
            logger.info("Terraform initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Terraform: {e}")
            return False
    
    def plan_terraform(self, var_file: Optional[str] = None) -> bool:
        """Create a Terraform plan."""
        try:
            logger.info("Creating Terraform plan...")
            command = ["plan"]
            if var_file:
                command.extend(["-var-file", var_file])
            
            result = self.run_terraform_command(command)
            logger.info("Terraform plan created successfully")
            print(result.stdout)
            return True
        except Exception as e:
            logger.error(f"Failed to create Terraform plan: {e}")
            return False
    
    def apply_terraform(self, var_file: Optional[str] = None, auto_approve: bool = False) -> bool:
        """Apply Terraform configuration."""
        try:
            logger.info("Applying Terraform configuration...")
            command = ["apply"]
            if var_file:
                command.extend(["-var-file", var_file])
            if auto_approve:
                command.append("-auto-approve")
            
            result = self.run_terraform_command(command, capture_output=False)
            logger.info("Terraform applied successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to apply Terraform: {e}")
            return False
    
    def destroy_terraform(self, var_file: Optional[str] = None, auto_approve: bool = False) -> bool:
        """Destroy Terraform-managed resources."""
        try:
            logger.info("Destroying Terraform resources...")
            command = ["destroy"]
            if var_file:
                command.extend(["-var-file", var_file])
            if auto_approve:
                command.append("-auto-approve")
            
            result = self.run_terraform_command(command, capture_output=False)
            logger.info("Terraform resources destroyed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to destroy Terraform resources: {e}")
            return False
    
    def show_outputs(self) -> Dict[str, Any]:
        """Get Terraform outputs."""
        try:
            logger.info("Getting Terraform outputs...")
            result = self.run_terraform_command(["output", "-json"])
            outputs = json.loads(result.stdout)
            return outputs
        except Exception as e:
            logger.error(f"Failed to get Terraform outputs: {e}")
            return {}
    
    def validate_terraform(self) -> bool:
        """Validate Terraform configuration."""
        try:
            logger.info("Validating Terraform configuration...")
            self.run_terraform_command(["validate"])
            logger.info("Terraform configuration is valid")
            return True
        except Exception as e:
            logger.error(f"Terraform validation failed: {e}")
            return False
    
    def create_lambda_package(self) -> bool:
        """Create Lambda deployment package."""
        try:
            logger.info("Creating Lambda deployment package...")
            
            if not self.lambda_source.exists():
                logger.error(f"Lambda source file not found: {self.lambda_source}")
                return False
            
            # Create a temporary directory for the package
            temp_dir = self.working_dir / "temp_lambda"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Copy the Lambda function
                shutil.copy2(self.lambda_source, temp_dir / "index.py")
                
                # Install dependencies if requirements.txt exists
                requirements_file = self.working_dir / "requirements.txt"
                if requirements_file.exists():
                    logger.info("Installing Lambda dependencies...")
                    subprocess.run([
                        "pip", "install", "-r", str(requirements_file),
                        "-t", str(temp_dir)
                    ], check=True)
                
                # Create zip file
                with zipfile.ZipFile(self.lambda_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"Lambda package created: {self.lambda_zip}")
                return True
                
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Failed to create Lambda package: {e}")
            return False
    
    def get_terraform_state(self) -> Dict[str, Any]:
        """Get current Terraform state."""
        try:
            result = self.run_terraform_command(["show", "-json"])
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Failed to get Terraform state: {e}")
            return {}
    
    def list_resources(self) -> List[str]:
        """List all resources in the current state."""
        state = self.get_terraform_state()
        resources = []
        
        if 'values' in state and 'root_module' in state['values']:
            for resource in state['values']['root_module'].get('resources', []):
                resources.append(f"{resource['type']}.{resource['name']}")
        
        return resources

def main():
    """Main entry point for the Terraform manager."""
    parser = argparse.ArgumentParser(description="Manage AWS IAM Solution with Terraform")
    parser.add_argument("command", choices=[
        "init", "plan", "apply", "destroy", "validate", "outputs", 
        "state", "resources", "package-lambda"
    ], help="Terraform command to execute")
    parser.add_argument("--var-file", help="Path to variables file")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve changes")
    parser.add_argument("--working-dir", default=".", help="Working directory for Terraform")
    
    args = parser.parse_args()
    
    # Initialize Terraform manager
    tf_manager = TerraformManager(args.working_dir)
    
    try:
        if args.command == "init":
            success = tf_manager.init_terraform()
        elif args.command == "plan":
            success = tf_manager.plan_terraform(args.var_file)
        elif args.command == "apply":
            success = tf_manager.apply_terraform(args.var_file, args.auto_approve)
        elif args.command == "destroy":
            success = tf_manager.destroy_terraform(args.var_file, args.auto_approve)
        elif args.command == "validate":
            success = tf_manager.validate_terraform()
        elif args.command == "outputs":
            outputs = tf_manager.show_outputs()
            print(json.dumps(outputs, indent=2))
            success = True
        elif args.command == "state":
            state = tf_manager.get_terraform_state()
            print(json.dumps(state, indent=2))
            success = True
        elif args.command == "resources":
            resources = tf_manager.list_resources()
            for resource in resources:
                print(resource)
            success = True
        elif args.command == "package-lambda":
            success = tf_manager.create_lambda_package()
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False
        
        if success:
            logger.info(f"Command '{args.command}' completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Command '{args.command}' failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()