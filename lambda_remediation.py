#!/usr/bin/env python3
"""
AWS IAM Remediation Lambda Function
This function processes Access Analyzer findings and provides automated remediation suggestions.
"""

import json
import boto3
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
accessanalyzer = boto3.client('accessanalyzer')
iam = boto3.client('iam')

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Access Analyzer findings.
    
    Args:
        event: EventBridge event containing Access Analyzer finding details
        context: Lambda context object
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract finding details from the event
        finding_id = event.get('detail', {}).get('id')
        analyzer_arn = event.get('detail', {}).get('analyzerArn')
        
        if not finding_id or not analyzer_arn:
            logger.error("Missing required fields in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing finding ID or analyzer ARN'})
            }
        
        # Get the finding details
        finding = get_finding(analyzer_arn, finding_id)
        if not finding:
            logger.error(f"Could not retrieve finding {finding_id}")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Finding not found'})
            }
        
        # Process the finding
        result = process_finding(finding)
        
        logger.info(f"Processed finding {finding_id}: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'findingId': finding_id,
                'result': result
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_finding(analyzer_arn: str, finding_id: str) -> Dict[str, Any]:
    """
    Retrieve finding details from Access Analyzer.
    
    Args:
        analyzer_arn: ARN of the Access Analyzer
        finding_id: ID of the finding to retrieve
        
    Returns:
        Finding details or None if not found
    """
    try:
        response = accessanalyzer.get_finding(
            analyzerArn=analyzer_arn,
            id=finding_id
        )
        return response.get('finding', {})
    except Exception as e:
        logger.error(f"Error retrieving finding {finding_id}: {str(e)}")
        return None

def process_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an Access Analyzer finding and provide remediation suggestions.
    
    Args:
        finding: Finding details from Access Analyzer
        
    Returns:
        Processing result with remediation suggestions
    """
    finding_type = finding.get('resourceType', '')
    status = finding.get('status', '')
    issue_code = finding.get('issueCode', '')
    
    logger.info(f"Processing finding: type={finding_type}, status={status}, issue={issue_code}")
    
    # Initialize result
    result = {
        'findingId': finding.get('id'),
        'resourceType': finding_type,
        'status': status,
        'issueCode': issue_code,
        'remediation': [],
        'riskLevel': 'UNKNOWN'
    }
    
    # Determine risk level based on finding type and issue
    result['riskLevel'] = assess_risk_level(finding_type, issue_code)
    
    # Generate remediation suggestions based on finding type
    if finding_type == 'AWS::IAM::Role':
        result['remediation'] = get_role_remediation(finding)
    elif finding_type == 'AWS::IAM::User':
        result['remediation'] = get_user_remediation(finding)
    elif finding_type == 'AWS::S3::Bucket':
        result['remediation'] = get_s3_remediation(finding)
    elif finding_type == 'AWS::KMS::Key':
        result['remediation'] = get_kms_remediation(finding)
    else:
        result['remediation'] = get_generic_remediation(finding)
    
    return result

def assess_risk_level(resource_type: str, issue_code: str) -> str:
    """
    Assess the risk level of a finding.
    
    Args:
        resource_type: Type of AWS resource
        issue_code: Specific issue code from the finding
        
    Returns:
        Risk level (HIGH, MEDIUM, LOW)
    """
    high_risk_issues = [
        'S3_BUCKET_PUBLIC_READ_ACCESS',
        'S3_BUCKET_PUBLIC_WRITE_ACCESS',
        'IAM_ROLE_ALLOWS_PUBLIC_ASSUMPTION',
        'KMS_KEY_WITH_SYMMETRIC_ENCRYPTION',
        'IAM_POLICY_ALLOWS_PUBLIC_ACCESS'
    ]
    
    medium_risk_issues = [
        'S3_BUCKET_LOGGING_DISABLED',
        'IAM_ROLE_OVERLY_PERMISSIVE',
        'KMS_KEY_ROTATION_DISABLED'
    ]
    
    if issue_code in high_risk_issues:
        return 'HIGH'
    elif issue_code in medium_risk_issues:
        return 'MEDIUM'
    else:
        return 'LOW'

def get_role_remediation(finding: Dict[str, Any]) -> List[str]:
    """Get remediation suggestions for IAM role findings."""
    issue_code = finding.get('issueCode', '')
    
    remediation = []
    
    if issue_code == 'IAM_ROLE_ALLOWS_PUBLIC_ASSUMPTION':
        remediation.extend([
            "Remove the public trust policy from the role",
            "Add conditions to restrict who can assume the role",
            "Consider using AWS Organizations SCPs to prevent public role assumption"
        ])
    elif issue_code == 'IAM_ROLE_OVERLY_PERMISSIVE':
        remediation.extend([
            "Review and reduce the permissions attached to the role",
            "Apply the principle of least privilege",
            "Use specific resource ARNs instead of wildcards where possible",
            "Consider using AWS managed policies instead of custom policies"
        ])
    else:
        remediation.append("Review the role's trust policy and attached permissions")
    
    return remediation

def get_user_remediation(finding: Dict[str, Any]) -> List[str]:
    """Get remediation suggestions for IAM user findings."""
    issue_code = finding.get('issueCode', '')
    
    remediation = []
    
    if issue_code == 'IAM_USER_UNUSED_ACCESS_KEY':
        remediation.extend([
            "Delete unused access keys",
            "Implement access key rotation policies",
            "Consider using IAM roles instead of access keys"
        ])
    elif issue_code == 'IAM_USER_UNUSED_CREDENTIALS':
        remediation.extend([
            "Remove unused credentials",
            "Implement credential lifecycle management",
            "Consider using AWS SSO for user access"
        ])
    else:
        remediation.append("Review user permissions and remove unnecessary access")
    
    return remediation

def get_s3_remediation(finding: Dict[str, Any]) -> List[str]:
    """Get remediation suggestions for S3 bucket findings."""
    issue_code = finding.get('issueCode', '')
    
    remediation = []
    
    if issue_code == 'S3_BUCKET_PUBLIC_READ_ACCESS':
        remediation.extend([
            "Remove public read access from the bucket policy",
            "Enable S3 Block Public Access settings",
            "Review and update bucket ACLs"
        ])
    elif issue_code == 'S3_BUCKET_PUBLIC_WRITE_ACCESS':
        remediation.extend([
            "Remove public write access from the bucket policy",
            "Enable S3 Block Public Access settings",
            "Implement proper access controls"
        ])
    elif issue_code == 'S3_BUCKET_LOGGING_DISABLED':
        remediation.extend([
            "Enable S3 server access logging",
            "Configure CloudTrail for S3 API calls",
            "Set up monitoring and alerting"
        ])
    else:
        remediation.append("Review bucket policies and access controls")
    
    return remediation

def get_kms_remediation(finding: Dict[str, Any]) -> List[str]:
    """Get remediation suggestions for KMS key findings."""
    issue_code = finding.get('issueCode', '')
    
    remediation = []
    
    if issue_code == 'KMS_KEY_WITH_SYMMETRIC_ENCRYPTION':
        remediation.extend([
            "Consider using asymmetric encryption for better security",
            "Review key usage patterns",
            "Implement proper key rotation"
        ])
    elif issue_code == 'KMS_KEY_ROTATION_DISABLED':
        remediation.extend([
            "Enable automatic key rotation",
            "Implement manual key rotation procedures",
            "Review key lifecycle management"
        ])
    else:
        remediation.append("Review KMS key policies and usage")
    
    return remediation

def get_generic_remediation(finding: Dict[str, Any]) -> List[str]:
    """Get generic remediation suggestions for other resource types."""
    return [
        "Review the resource's access policies",
        "Apply the principle of least privilege",
        "Consider using AWS Organizations SCPs for additional controls",
        "Implement monitoring and alerting for this resource type"
    ]