# aws_iam_solution/constructs/organization_construct.py
from constructs import Construct
from aws_cdk import (
    aws_organizations as organizations,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput,
)

class OrganizationConstruct(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        # Create Organization
        self.organization = organizations.CfnOrganization(
            self, "Organization",
            feature_set="ALL"  # Enables all features including SCPs
        )

        # Create Security OU
        self.security_ou = organizations.CfnOrganizationalUnit(
            self, "SecurityOU",
            parent_id=self.organization.attr_root_id,  # Reference to the root ID
            name="Security"
        )

        # Create SCP
        self.mfa_policy = organizations.CfnPolicy(
            self, "MFAPolicy",
            content={
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "RequireMFA",
                    "Effect": "Deny",
                    "NotAction": [
                        "iam:CreateVirtualMFADevice",
                        "iam:EnableMFADevice",
                        "iam:GetUser",
                        "iam:ListMFADevices",
                        "iam:ListVirtualMFADevices",
                        "iam:ResyncMFADevice"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "BoolIfExists": {
                            "aws:MultiFactorAuthPresent": "false"
                        }
                    }
                }]
            },
            name="require-mfa",
            type="SERVICE_CONTROL_POLICY"
        )

        # Output the Organization ID and Root ID
        CfnOutput(
            self,
            "OrganizationId",
            value=self.organization.attr_id,
            description="The ID of the AWS Organization"
        )

        CfnOutput(
            self,
            "OrganizationRootId",
            value=self.organization.attr_root_id,
            description="The Root ID of the AWS Organization"
        )

    def attach_policy_to_ou(self, policy_id: str, target_id: str):
        return organizations.CfnPolicyAttachment(
            self,
            f"PolicyAttachment-{policy_id}-{target_id}",
            policy_id=policy_id,
            target_id=target_id
        )
