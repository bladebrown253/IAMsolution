# AWS IAM Advanced Strategy (CDK)

This solution deploys an advanced, multi-account IAM strategy using AWS Organizations, Service Control Policies (SCPs), AWS IAM Identity Center (SSO) with ABAC, security logging/monitoring, IAM Access Analyzer with automated remediation, and optional JIT access workflow scaffolding.

## What it deploys

- Organizational structure with OUs: `Security`, `SharedServices`, `Workloads` (and `Prod`, `Dev`, `Sandbox` under `Workloads`).
- Advanced SCPs: require MFA, deny non-allowed regions, protect security services, deny root usage, enforce mandatory tags for ABAC.
- IAM Identity Center (SSO): ABAC attributes (department, costCenter, environment, jobFunction), permission sets (Admin, PowerUser, ReadOnly, Developer with ABAC inline policy), session duration controls.
- Monitoring and Logging: Organization CloudTrail (multi-region) to S3 and CloudWatch Logs, metric filters + alarms (root usage, console failures), AWS Config Organization Rules.
- Access Analyzer: organization analyzer with EventBridge -> Lambda remediation for public S3.
- Credential hygiene: daily Lambda to deactivate access keys older than 90 days.
- JIT Access: Step Functions scaffold with grant/revoke Lambdas (placeholders) for temporary elevated access.

## Architecture

```mermaid
flowchart TD
    subgraph AWS Organizations
      ROOT[Org Root]
      OU1[Security OU]
      OU2[Shared Services OU]
      OU3[Workloads OU]
      OU4[Prod OU]
      OU5[Dev OU]
      OU6[Sandbox OU]
      ROOT --> OU1
      ROOT --> OU2
      ROOT --> OU3
      OU3 --> OU4
      OU3 --> OU5
      OU3 --> OU6
      SCPs[SCPs: MFA, Region Deny, Protect Security, Deny Root, Tag Enforcement]
      SCPs --> ROOT
      TagEnf[Tag Enforcement] --> OU3
    end

    IdC[Identity Center (SSO) + ABAC]
    PS1[Admin PS]
    PS2[PowerUser PS]
    PS3[ReadOnly PS]
    PS4[Developer PS (ABAC)]
    IdC --> PS1
    IdC --> PS2
    IdC --> PS3
    IdC --> PS4

    subgraph Logging & Monitoring
      CT[Org CloudTrail -> S3 + CW Logs]
      MF[Metric Filters + Alarms]
      CFG[AWS Config Org Rules]
    end
    CT --> MF

    AA[Access Analyzer (Org)] --> EVB[EventBridge]
    EVB --> REM[Remediation Lambda]

    subgraph JIT Access
      SM[Step Functions]
      GR[Grant Lambda]
      RV[Revoke Lambda]
      SM --> GR --> RV
    end
```

## Prerequisites

- CDK v2 bootstrap in management account and region.
- Administrator privileges in the management account to manage Organizations, CloudTrail, Config, SSO.

## Deploy

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd AWS-IAM-Solution
cdk synth
cdk deploy
```

Note: IAM Identity Center external IdP integration (e.g., Okta SAML/OIDC or AWS Managed Microsoft AD) must be configured in the console; ABAC attributes map to the user attributes defined in your IdP (e.g., `user.department`, `user.costCenter`).

## Security defaults

- MFA required via SCP across the org.
- Session duration reduced for privileged sets; long-lived credentials deactivated automatically after 90 days.
- Organization-wide CloudTrail, Config rules, and Access Analyzer enable continuous monitoring.

## Operations

- Remediation Lambda auto-hardens public S3 buckets when flagged by Access Analyzer.
- Daily key hygiene runs at 03:00 UTC.
- Extend JIT by wiring approvals (e.g., SNS/Slack) and implementing `sso-admin` calls in Grant/Revoke Lambdas.
