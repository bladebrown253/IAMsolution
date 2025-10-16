#!/usr/bin/env python3
"""
Terraform Configuration Validator
This script performs basic validation of the Terraform configuration files.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

class TerraformValidator:
    """Validates Terraform configuration files."""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.errors = []
        self.warnings = []
    
    def validate_file_exists(self, filename: str) -> bool:
        """Check if a required file exists."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            self.errors.append(f"Required file not found: {filename}")
            return False
        return True
    
    def validate_json_syntax(self, filename: str) -> bool:
        """Validate JSON syntax in a file."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return True
        
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON syntax error in {filename}: {e}")
            return False
    
    def validate_terraform_syntax(self, filename: str) -> bool:
        """Basic Terraform syntax validation."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return True
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for basic Terraform syntax issues
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for unclosed quotes
                if line.count('"') % 2 != 0:
                    self.errors.append(f"Unclosed quotes in {filename} at line {i}")
                
                # Check for resource blocks
                if line.startswith('resource '):
                    if not re.match(r'resource\s+"[^"]+"\s+"[^"]+"\s*{', line):
                        self.errors.append(f"Invalid resource syntax in {filename} at line {i}")
                
                # Check for data blocks
                if line.startswith('data '):
                    if not re.match(r'data\s+"[^"]+"\s+"[^"]+"\s*{', line):
                        self.errors.append(f"Invalid data syntax in {filename} at line {i}")
            
            return True
        except Exception as e:
            self.errors.append(f"Error reading {filename}: {e}")
            return False
    
    def validate_variables_references(self) -> bool:
        """Check that all variable references are defined."""
        main_tf = self.config_dir / "main.tf"
        variables_tf = self.config_dir / "variables.tf"
        
        if not main_tf.exists() or not variables_tf.exists():
            return True
        
        # Extract variable references from main.tf
        with open(main_tf, 'r') as f:
            main_content = f.read()
        
        var_refs = re.findall(r'var\.(\w+)', main_content)
        
        # Extract variable definitions from variables.tf
        with open(variables_tf, 'r') as f:
            variables_content = f.read()
        
        var_defs = re.findall(r'variable\s+"(\w+)"', variables_content)
        
        # Check for undefined variables
        for var_ref in set(var_refs):
            if var_ref not in var_defs:
                self.warnings.append(f"Variable 'var.{var_ref}' is referenced but not defined")
        
        return True
    
    def validate_outputs_references(self) -> bool:
        """Check that all output references exist."""
        outputs_tf = self.config_dir / "outputs.tf"
        main_tf = self.config_dir / "main.tf"
        
        if not outputs_tf.exists() or not main_tf.exists():
            return True
        
        # Extract output references from outputs.tf
        with open(outputs_tf, 'r') as f:
            outputs_content = f.read()
        
        output_refs = re.findall(r'(\w+\.\w+)', outputs_content)
        
        # Extract resource names from main.tf
        with open(main_tf, 'r') as f:
            main_content = f.read()
        
        resource_names = re.findall(r'resource\s+"[^"]+"\s+"(\w+)"', main_content)
        data_names = re.findall(r'data\s+"[^"]+"\s+"(\w+)"', main_content)
        
        all_names = set(resource_names + data_names)
        
        # Check for undefined references
        for ref in set(output_refs):
            resource_name = ref.split('.')[0]
            if resource_name not in all_names:
                self.warnings.append(f"Output references undefined resource: {ref}")
        
        return True
    
    def validate_govcloud_compatibility(self) -> bool:
        """Check for GovCloud compatibility issues."""
        main_tf = self.config_dir / "main.tf"
        if not main_tf.exists():
            return True
        
        with open(main_tf, 'r') as f:
            content = f.read()
        
        # Check for GovCloud-specific ARN patterns
        if 'arn:aws-us-gov:' not in content:
            self.warnings.append("No GovCloud ARNs found - ensure all ARNs use 'arn:aws-us-gov:' prefix")
        
        # Check for GovCloud region
        if 'us-gov-west-1' not in content:
            self.warnings.append("GovCloud region not found - ensure region is set to 'us-gov-west-1'")
        
        return True
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Validating Terraform configuration...")
        
        # Check required files
        required_files = ["main.tf", "variables.tf", "outputs.tf"]
        for file in required_files:
            self.validate_file_exists(file)
        
        # Validate syntax
        for file in required_files:
            self.validate_terraform_syntax(file)
        
        # Validate variable references
        self.validate_variables_references()
        
        # Validate output references
        self.validate_outputs_references()
        
        # Validate GovCloud compatibility
        self.validate_govcloud_compatibility()
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'valid': len(self.errors) == 0
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print validation results."""
        print("\n" + "="*50)
        print("VALIDATION RESULTS")
        print("="*50)
        
        if results['valid']:
            print("✅ Configuration is valid!")
        else:
            print("❌ Configuration has errors!")
        
        if results['errors']:
            print(f"\n🚨 ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  • {error}")
        
        if results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  • {warning}")
        
        print("\n" + "="*50)

def main():
    """Main validation function."""
    validator = TerraformValidator()
    results = validator.validate_all()
    validator.print_results(results)
    
    if not results['valid']:
        exit(1)
    else:
        print("🎉 All validations passed!")

if __name__ == "__main__":
    main()