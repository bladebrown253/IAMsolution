# aws_iam_solution/aws_iam_solution_stack.py
from constructs import Construct
from aws_cdk import Stack
from aws_iam_solution.constructs.organization_construct import OrganizationConstruct
from aws_iam_solution.constructs.identity_center_construct import IdentityCenterConstruct
from aws_iam_solution.constructs.monitoring_construct import MonitoringConstruct

class AwsIamSolutionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Deploy Organization structure with advanced SCPs
        org_construct = OrganizationConstruct(self, "OrgConstruct", allowed_regions=["us-east-1", "us-west-2"]) 

        # Deploy Identity Center (SSO) configuration
        identity_center = IdentityCenterConstruct(
            self, 
            "IdentityCenter",
            org_construct.organization
        )

        # Example of adding an extra permission set via helper (if needed)
        # extra_ps = identity_center.create_permission_set(
        #     "DataScientist",
        #     [
        #         "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        #         "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
        #     ],
        #     session_duration="PT4H",
        # )

        # Deploy IAM monitoring and automation
        monitoring = MonitoringConstruct(
            self,
            "IAMMonitoring",
            org_construct.organization
        )
