# aws_iam_solution/constructs/monitoring_construct.py
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_accessanalyzer as accessanalyzer,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
)
from pathlib import Path

class MonitoringConstruct(Construct):
    def __init__(self, scope: Construct, id: str, organization):
        super().__init__(scope, id)
        
        # Create IAM Access Analyzer (AWS::AccessAnalyzer::Analyzer)
        self.analyzer = accessanalyzer.CfnAnalyzer(
            self, 
            "OrgAccessAnalyzer",
            analyzer_name="org-analyzer",
            type="ORGANIZATION"  # This requires the organization to be set up first
        )

        # Create Lambda for automated remediation
        asset_path = (Path(__file__).resolve().parents[1] / "lambda" / "remediation")
        self.remediation_function = lambda_.Function(
            self, 
            "RemediationFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset(str(asset_path)),
            timeout=Duration.minutes(5)
        )

        # Create EventBridge rule
        events.Rule(
            self, 
            "AccessAnalyzerFindings",
            event_pattern=events.EventPattern(
                source=["aws.access-analyzer"],
                detail_type=["Access Analyzer Finding"]
            ),
            targets=[targets.LambdaFunction(self.remediation_function)]
        )
