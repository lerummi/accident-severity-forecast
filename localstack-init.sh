#!/bin/bash

# Create MLflow S3 bucket
awslocal s3api \
        create-bucket --bucket mlflow-bucket \
        --create-bucket-configuration LocationConstraint=eu-central-1 \
        --region eu-central-1