# aws_iam_solution/constructs/organization_construct.py
from constructs import Construct
from aws_cdk import (
    aws_organizations as organizations,
    aws_iam as iam,
    CfnOutput,
)

class OrganizationConstruct(Construct):
    def __init__(self, scope: Construct, id: str, allowed_regions: list[str] | None = None):
        super().__init__(scope, id)

        # Parameters / defaults
        self.allowed_regions = allowed_regions or ["us-east-1", "us-west-2"]

        # Create Organization
        self.organization = organizations.CfnOrganization(
            self,
            "Organization",
            feature_set="ALL",  # Enables all features including SCPs
        )

        # Create top-level OUs
        self.security_ou = organizations.CfnOrganizationalUnit(
            self,
            "SecurityOU",
            parent_id=self.organization.attr_root_id,
            name="Security",
        )

        self.shared_services_ou = organizations.CfnOrganizationalUnit(
            self,
            "SharedServicesOU",
            parent_id=self.organization.attr_root_id,
            name="SharedServices",
        )

        self.workloads_ou = organizations.CfnOrganizationalUnit(
            self,
            "WorkloadsOU",
            parent_id=self.organization.attr_root_id,
            name="Workloads",
        )

        # Child OUs under Workloads
        self.prod_ou = organizations.CfnOrganizationalUnit(
            self,
            "ProdOU",
            parent_id=self.workloads_ou.ref,
            name="Prod",
        )
        self.dev_ou = organizations.CfnOrganizationalUnit(
            self,
            "DevOU",
            parent_id=self.workloads_ou.ref,
            name="Dev",
        )
        self.sandbox_ou = organizations.CfnOrganizationalUnit(
            self,
            "SandboxOU",
            parent_id=self.workloads_ou.ref,
            name="Sandbox",
        )

        # --- Service Control Policies (SCPs) ---
        # Require MFA for all actions except enabling/configuring MFA
        self.mfa_policy = organizations.CfnPolicy(
            self,
            "MFAPolicy",
            content={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "RequireMFA",
                        "Effect": "Deny",
                        "NotAction": [
                            "iam:CreateVirtualMFADevice",
                            "iam:EnableMFADevice",
                            "iam:GetUser",
                            "iam:ListMFADevices",
                            "iam:ListVirtualMFADevices",
                            "iam:ResyncMFADevice",
                            "sts:GetSessionToken",
                        ],
                        "Resource": "*",
                        "Condition": {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}},
                    }
                ],
            },
            name="require-mfa",
            type="SERVICE_CONTROL_POLICY",
            target_ids=[self.organization.attr_root_id],
        )

        # Deny usage outside approved regions
        self.deny_unsupported_regions = organizations.CfnPolicy(
            self,
            "DenyUnsupportedRegions",
            content={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyRegionsNotAllowed",
                        "Effect": "Deny",
                        "Action": "*",
                        "Resource": "*",
                        "Condition": {
                            "StringNotEquals": {"aws:RequestedRegion": self.allowed_regions}
                        },
                    }
                ],
            },
            name="deny-unsupported-regions",
            type="SERVICE_CONTROL_POLICY",
            target_ids=[self.organization.attr_root_id],
        )

        # Deny changes to critical security services
        self.protect_security_services = organizations.CfnPolicy(
            self,
            "ProtectSecurityServices",
            content={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyDisablingSecurityServices",
                        "Effect": "Deny",
                        "Action": [
                            "cloudtrail:DeleteTrail",
                            "cloudtrail:StopLogging",
                            "cloudtrail:UpdateTrail",
                            "config:DeleteConfigurationRecorder",
                            "config:StopConfigurationRecorder",
                            "config:DeleteDeliveryChannel",
                            "guardduty:DeleteDetector",
                            "guardduty:StopMonitoringMembers",
                            "access-analyzer:DeleteAnalyzer",
                        ],
                        "Resource": "*",
                    }
                ],
            },
            name="protect-security-services",
            type="SERVICE_CONTROL_POLICY",
            target_ids=[self.organization.attr_root_id],
        )

        # Enforce tagging at creation time for ABAC enablement
        self.enforce_mandatory_tags = organizations.CfnPolicy(
            self,
            "EnforceMandatoryTags",
            content={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyCreateWithoutTags",
                        "Effect": "Deny",
                        "Action": [
                            "ec2:RunInstances",
                            "ec2:Create*",
                            "rds:Create*",
                            "s3:CreateBucket",
                            "lambda:CreateFunction",
                            "logs:CreateLogGroup",
                        ],
                        "Resource": "*",
                        "Condition": {
                            "ForAllValues:StringEqualsIfExists": {
                                "aws:TagKeys": ["department", "costCenter", "environment"]
                            }
                        },
                    }
                ],
            },
            name="enforce-mandatory-tags",
            type="SERVICE_CONTROL_POLICY",
            target_ids=[self.workloads_ou.ref],
        )

        # Deny root user usage
        self.deny_root_user = organizations.CfnPolicy(
            self,
            "DenyRootUser",
            content={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyRootUser",
                        "Effect": "Deny",
                        "Action": "*",
                        "Resource": "*",
                        "Condition": {
                            "StringLike": {"aws:PrincipalArn": "arn:aws:iam::*:root"}
                        },
                    }
                ],
            },
            name="deny-root-user",
            type="SERVICE_CONTROL_POLICY",
            target_ids=[self.organization.attr_root_id],
        )


        # Output helpful identifiers
        CfnOutput(
            self,
            "OrganizationId",
            value=self.organization.attr_id,
            description="The ID of the AWS Organization",
        )
        CfnOutput(
            self,
            "OrganizationRootId",
            value=self.organization.attr_root_id,
            description="The Root ID of the AWS Organization",
        )
        CfnOutput(self, "SecurityOuId", value=self.security_ou.ref)
        CfnOutput(self, "SharedServicesOuId", value=self.shared_services_ou.ref)
        CfnOutput(self, "WorkloadsOuId", value=self.workloads_ou.ref)
        CfnOutput(self, "ProdOuId", value=self.prod_ou.ref)
        CfnOutput(self, "DevOuId", value=self.dev_ou.ref)
        CfnOutput(self, "SandboxOuId", value=self.sandbox_ou.ref)

    def attach_policy_to_ou(self, policy_id: str, target_id: str):
        return organizations.CfnPolicyAttachment(
            self,
            f"PolicyAttachment-{policy_id}-{target_id}",
            policy_id=policy_id,
            target_id=target_id,
        )
