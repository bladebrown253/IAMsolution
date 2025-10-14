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
            name="MainIdentityCenter"
        )

        # Create Permission Sets using tuple for managed policies
        admin_policies: Sequence[str] = tuple(["arn:aws:iam::aws:policy/AdministratorAccess"])
        
        self.admin_permission_set = sso.CfnPermissionSet(
            self, 
            "AdminPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="AdminAccess",
            session_duration="PT4H",
            managed_policies=admin_policies
        )

        # Create ReadOnly Permission Set
        readonly_policies: Sequence[str] = tuple(["arn:aws:iam::aws:policy/ReadOnlyAccess"])
        
        self.readonly_permission_set = sso.CfnPermissionSet(
            self,
            "ReadOnlyPermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name="ReadOnlyAccess",
            session_duration="PT4H",
            managed_policies=readonly_policies
        )

        # Output the Identity Center ARN
        CfnOutput(
            self, 
            "IdentityCenterArn",
            value=self.identity_center.attr_instance_arn,
            description="The ARN of the Identity Center instance"
        )

    def create_permission_set(self, name: str, policies: List[str], session_duration: str = "PT4H"):
        managed_policies: Sequence[str] = tuple(policies)
        return sso.CfnPermissionSet(
            self,
            f"{name}PermissionSet",
            instance_arn=self.identity_center.attr_instance_arn,
            name=name,
            session_duration=session_duration,
            managed_policies=managed_policies
        )
