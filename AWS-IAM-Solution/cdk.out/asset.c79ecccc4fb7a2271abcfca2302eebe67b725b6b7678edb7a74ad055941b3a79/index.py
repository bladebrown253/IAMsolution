import json
import boto3
import os

s3 = boto3.client("s3")


def handler(event, context):
    # Basic remediation example: if Access Analyzer finding indicates public S3 bucket,
    # enforce PublicAccessBlock and attempt to remove public statements.
    detail = event.get("detail", {})
    finding = detail.get("finding", {})
    resource_type = finding.get("resourceType")
    resource = finding.get("resource")

    if resource_type == "AWS::S3::Bucket" and resource:
        bucket_name = resource.split(":")[-1]
        try:
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
        except Exception as e:
            print(f"Failed to set PublicAccessBlock on {bucket_name}: {e}")

        try:
            # Fetch existing policy and strip statements that allow Principal: '*'
            policy_resp = s3.get_bucket_policy(Bucket=bucket_name)
            policy_doc = json.loads(policy_resp["Policy"])
            statements = policy_doc.get("Statement", [])
            filtered = []
            for stmt in statements:
                principal = stmt.get("Principal")
                effect = stmt.get("Effect")
                if effect == "Allow" and (principal == "*" or principal == {"AWS": "*"}):
                    # drop overly permissive statement
                    continue
                filtered.append(stmt)
            policy_doc["Statement"] = filtered
            s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy_doc))
        except s3.exceptions.NoSuchBucketPolicy:
            pass
        except Exception as e:
            print(f"Failed to adjust bucket policy for {bucket_name}: {e}")

    # Always log the event for audit trail
    print(json.dumps(event))
    return {"status": "ok"}
