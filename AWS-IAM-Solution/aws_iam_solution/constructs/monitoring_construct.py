# aws_iam_solution/constructs/monitoring_construct.py
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_accessanalyzer as accessanalyzer,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudtrail as cloudtrail,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_config as config,
    aws_s3 as s3,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    Duration,
    RemovalPolicy,
)
from pathlib import Path

class MonitoringConstruct(Construct):
    def __init__(self, scope: Construct, id: str, organization):
        super().__init__(scope, id)

        # --- IAM Access Analyzer for org ---
        self.analyzer = accessanalyzer.CfnAnalyzer(
            self,
            "OrgAccessAnalyzer",
            analyzer_name="org-analyzer",
            type="ORGANIZATION",
        )

        # --- CloudTrail: Organization trail, multi-region, to S3 and CloudWatch Logs ---
        logs_group = logs.LogGroup(
            self,
            "CloudTrailLogGroup",
            retention=logs.RetentionDays.TWO_YEARS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        log_bucket = s3.Bucket(
            self,
            "CloudTrailBucket",
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
        )

        trail = cloudtrail.Trail(
            self,
            "OrganizationTrail",
            bucket=log_bucket,
            is_multi_region_trail=True,
            is_organization_trail=True,
            send_to_cloud_watch_logs=True,
            cloud_watch_log_group=logs_group,
            include_global_service_events=True,
        )
        trail.log_all_lambda_data_events()
        trail.log_all_s3_data_events()

        # --- CloudWatch Metric Filters + Alarms on CloudTrail logs ---
        # Console sign-in failures
        signin_failure_metric = logs.MetricFilter(
            self,
            "ConsoleSignInFailureFilter",
            log_group=logs_group,
            metric_namespace="Security/IAM",
            metric_name="ConsoleSignInFailureCount",
            filter_pattern=logs.FilterPattern.literal("{ ($.eventName = ConsoleLogin) && ($.errorMessage = \"Failed authentication\") }"),
            metric_value="1",
        ).metric()
        cloudwatch.Alarm(
            self,
            "ConsoleSignInFailureAlarm",
            metric=signin_failure_metric,
            evaluation_periods=1,
            threshold=5,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Root account usage
        root_usage_metric = logs.MetricFilter(
            self,
            "RootUsageFilter",
            log_group=logs_group,
            metric_namespace="Security/IAM",
            metric_name="RootUsageCount",
            filter_pattern=logs.FilterPattern.literal("{ ($.userIdentity.type = \"Root\") && ($.eventType != \"AwsServiceEvent\") }"),
            metric_value="1",
        ).metric()
        cloudwatch.Alarm(
            self,
            "RootUsageAlarm",
            metric=root_usage_metric,
            evaluation_periods=1,
            threshold=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
        )

        # --- AWS Config Organization Managed Rules ---
        config_rules = [
            ("CloudTrailEnabled", "CLOUD_TRAIL_ENABLED", None),
            ("IamUserMfaEnabled", "IAM_USER_MFA_ENABLED", None),
            ("RootMfaEnabled", "ROOT_ACCOUNT_MFA_ENABLED", None),
            ("S3PublicReadProhibited", "S3_BUCKET_PUBLIC_READ_PROHIBITED", None),
            ("S3PublicWriteProhibited", "S3_BUCKET_PUBLIC_WRITE_PROHIBITED", None),
        ]
        for logical_id, rule_name, params in config_rules:
            config.CfnOrganizationConfigRule(
                self,
                f"OrgRule{logical_id}",
                organization_managed_rule_metadata=config.CfnOrganizationConfigRule.OrganizationManagedRuleMetadataProperty(
                    rule_identifier=rule_name,
                    input_parameters=params,
                ),
                organization_config_rule_name=f"org-{rule_name.lower()}",
            )

        # --- Access Analyzer Finding Remediation ---
        remediation_asset_path = (Path(__file__).resolve().parents[1] / "lambda" / "remediation")
        self.remediation_function = lambda_.Function(
            self,
            "RemediationFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset(str(remediation_asset_path)),
            timeout=Duration.minutes(5),
        )
        self.remediation_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetBucketPolicy",
                    "s3:PutBucketPolicy",
                    "s3:PutBucketPublicAccessBlock",
                    "s3:GetBucketPublicAccessBlock",
                    "s3:ListAllMyBuckets",
                ],
                resources=["*"],
            )
        )

        events.Rule(
            self,
            "AccessAnalyzerFindings",
            event_pattern=events.EventPattern(
                source=["aws.access-analyzer"],
                detail_type=["Access Analyzer Finding"],
            ),
            targets=[targets.LambdaFunction(self.remediation_function)],
        )

        # --- Credential hygiene: deactivate stale access keys ---
        rotation_fn = lambda_.Function(
            self,
            "CredentialRotationFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                """
import boto3, datetime, json
iam = boto3.client('iam')

def handler(event, context):
    paginator = iam.get_paginator('list_users')
    now = datetime.datetime.now(datetime.timezone.utc)
    disabled = []
    for page in paginator.paginate():
        for user in page['Users']:
            access_keys = iam.list_access_keys(UserName=user['UserName']).get('AccessKeyMetadata', [])
            for key in access_keys:
                age_days = (now - key['CreateDate']).days
                if age_days > 90 and key['Status'] == 'Active':
                    iam.update_access_key(UserName=user['UserName'], AccessKeyId=key['AccessKeyId'], Status='Inactive')
                    disabled.append({'user': user['UserName'], 'key': key['AccessKeyId'], 'ageDays': age_days})
    print(json.dumps({'disabled': disabled}))
    return {'disabledCount': len(disabled)}
                """
            ),
            timeout=Duration.minutes(5),
        )
        rotation_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:ListUsers",
                    "iam:ListAccessKeys",
                    "iam:UpdateAccessKey",
                ],
                resources=["*"],
            )
        )

        # Daily schedule for credential hygiene
        events.Rule(
            self,
            "DailyCredentialRotation",
            schedule=events.Schedule.cron(minute="0", hour="3"),
            targets=[targets.LambdaFunction(rotation_fn)],
        )

        # --- JIT Access workflow (scaffold) ---
        # Request -> manager approval (manual task) -> grant temporary admin via IAM Identity Center PermissionSet -> revoke
        grant_lambda = lambda_.Function(
            self,
            "JitGrantFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                """
import json

def handler(event, context):
    # Placeholder: integrate with sso-admin to provision a temporary assignment
    # Record ticket/reference for audit
    print(json.dumps(event))
    return {'granted': True}
                """
            ),
            timeout=Duration.minutes(5),
        )
        revoke_lambda = lambda_.Function(
            self,
            "JitRevokeFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                """
import json

def handler(event, context):
    # Placeholder: remove temporary assignment via sso-admin
    print(json.dumps(event))
    return {'revoked': True}
                """
            ),
            timeout=Duration.minutes(5),
        )

        approve = sfn.Pass(self, "ManagerApproved")
        grant = tasks.LambdaInvoke(self, "GrantTempAccess", lambda_function=grant_lambda, output_path="$.Payload")
        wait = sfn.Wait(self, "WaitDuration", time=sfn.WaitTime.duration(Duration.minutes(30)))
        revoke = tasks.LambdaInvoke(self, "RevokeAccess", lambda_function=revoke_lambda, output_path="$.Payload")

        definition = approve.next(grant).next(wait).next(revoke)
        sfn.StateMachine(
            self,
            "JitAccessStateMachine",
            definition=definition,
            timeout=Duration.hours(2),
        )
