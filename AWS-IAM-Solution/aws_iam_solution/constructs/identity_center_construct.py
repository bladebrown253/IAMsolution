# aws_iam_solution/constructs/identity_center_construct.py
from constructs import Construct
from aws_cdk import (
    aws_sso as sso,
    aws_iam as iam,
    CfnOutput,
)
from typing import Sequence, List

class IdentityCenterConstruct(Construct):
    def __init__(self, scope: Construct, id: str, organization):
        super().__init__(scope, id)

        # Enable AWS IAM Identity Center
        self.identity_center = sso.CfnInstance(
            self,
            "IdentityCenter",
            name="MainIdentityCenter",
        )

        # Enable ABAC by configuring access control attributes that will be
        # sourced from the external IdP (e.g., Okta user profile attributes)
        sso.CfnInstanceAccessControlAttributeConfiguration(
            self,
            "ABACAttributes",
            instance_arn=self.identity_center.attr_instance_arn,
            access_control_attributes=[
                sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeProperty(
                    key="department",
                    value=sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeValueProperty(
                        source=["user.department"]
                    ),
                ),
                sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeProperty(
                    key="costCenter",
                    value=sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeValueProperty(
                        source=["user.costCenter"]
                    ),
                ),
                sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeProperty(
                    key="environment",
                    value=sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeValueProperty(
                        source=["user.environment"]
                    ),
                ),
                sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeProperty(
                    key="jobFunction",
                    value=sso.CfnInstanceAccessControlAttributeConfiguration.AccessControlAttributeValueProperty(
                        source=["user.title"]
                    ),
                ),
            ],
        )

        # --- Permission Sets ---
        # Administrator with tighter session duration
        admin_policies: List[str] = ["arn:aws:iam::aws:policy/AdministratorAccess"]
        self.admin_permission_set = sso.CfnPermissionSet(
            self,
            "AdminPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="AdminAccess",
            session_duration="PT1H",
            managed_policies=admin_policies,
        )

        # PowerUser with 2h sessions
        power_policies: List[str] = ["arn:aws:iam::aws:policy/PowerUserAccess"]
        self.poweruser_permission_set = sso.CfnPermissionSet(
            self,
            "PowerUserPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="PowerUserAccess",
            session_duration="PT2H",
            managed_policies=power_policies,
        )

        # ReadOnly with longer sessions
        readonly_policies: List[str] = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
        self.readonly_permission_set = sso.CfnPermissionSet(
            self,
            "ReadOnlyPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="ReadOnlyAccess",
            session_duration="PT8H",
            managed_policies=readonly_policies,
        )

        # Developer role with ABAC-based resource scoping
        developer_inline_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowTaggingForOwnership",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:CreateTags",
                        "ec2:DeleteTags",
                        "s3:PutBucketTagging",
                        "lambda:TagResource",
                        "lambda:UntagResource",
                    ],
                    "Resource": "*",
                    "Condition": {
                        "ForAllValues:StringEquals": {
                            "aws:TagKeys": ["department", "environment"]
                        },
                        "StringEquals": {
                            "aws:RequestTag/department": "${aws:PrincipalTag/department}",
                            "aws:RequestTag/environment": "${aws:PrincipalTag/environment}",
                        },
                    },
                },
                {
                    "Sid": "AllowS3PerDept",
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListAllMyBuckets",
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:ResourceTag/department": "${aws:PrincipalTag/department}",
                            "aws:ResourceTag/environment": "${aws:PrincipalTag/environment}"
                        }
                    },
                },
                {
                    "Sid": "DescribeOnly",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:Describe*",
                        "rds:Describe*",
                        "cloudwatch:Get*",
                        "cloudwatch:List*"
                    ],
                    "Resource": "*",
                },
            ],
        }
        dev_policies: List[str] = [
            "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
            "arn:aws:iam::aws:policy/AWSCloudFormationReadOnlyAccess",
        ]
        self.developer_permission_set = sso.CfnPermissionSet(
            self,
            "DeveloperPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="DeveloperAccess",
            session_duration="PT4H",
            managed_policies=dev_policies,
            inline_policy=developer_inline_policy,
        )

        # Output the Identity Center ARN and key permission sets
        CfnOutput(
            self,
            "IdentityCenterArn",
            value=self.identity_center.attr_instance_arn,
            description="The ARN of the Identity Center instance",
        )
        CfnOutput(self, "AdminPermissionSetArn", value=self.admin_permission_set.attr_permission_set_arn)
        CfnOutput(self, "PowerUserPermissionSetArn", value=self.poweruser_permission_set.attr_permission_set_arn)
        CfnOutput(self, "ReadOnlyPermissionSetArn", value=self.readonly_permission_set.attr_permission_set_arn)
        CfnOutput(self, "DeveloperPermissionSetArn", value=self.developer_permission_set.attr_permission_set_arn)

    def create_permission_set(self, name: str, policies: List[str], session_duration: str = "PT4H"):
        managed_policies: List[str] = list(policies)
        return sso.CfnPermissionSet(
            self,
            f"{name}PermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name=name,
            session_duration=session_duration,
            managed_policies=managed_policies,
        )
