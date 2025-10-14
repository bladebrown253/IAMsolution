#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_iam_solution.aws_iam_solution_stack import AwsIamSolutionStack

app = cdk.App()
AwsIamSolutionStack(app, "AwsIamSolutionStack")
app.synth()
