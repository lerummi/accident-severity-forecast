#!/bin/bash

echo "Restoring from pod"
FILE=/pods/main
if test -f "$FILE"; then
  localstack pod load file://${FILE}
else
  echo "No pod state found"
fi

# Create MLflow S3 bucket
if awslocal s3 ls "s3://mlflow-bucket" 2>&1 | grep -q 'NoSuchBucket';
then
        echo "Bucket does not exist, creating ..."
        awslocal s3api \
                create-bucket --bucket mlflow-bucket \
                --create-bucket-configuration LocationConstraint=eu-central-1 \
                --region eu-central-1
fi

# Create Dagster storage bucket
if awslocal s3 ls "s3://accident-severity-workflow-data" 2>&1 | grep -q 'NoSuchBucket';
then
        echo "Bucket does not exist, creating ..."
        awslocal s3api \
                create-bucket --bucket accident-severity-workflow-data \
                --create-bucket-configuration LocationConstraint=eu-central-1 \
                --region eu-central-1
fi