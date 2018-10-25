#!/bin/bash

set -e

LABEL='zap-lambda'
BUILD_DIR="./_builds/"
HERE=$(pwd)
BUCKET="$1"
ARTIFACT="$2"
REGION=us-west-2


if [[ -z "${ARTIFACT}" ]]
then
	ARTIFACT=$(find ./_builds -maxdepth 1 -type f -name 'zap*.zip' | sort | tail -n1)
fi

if [[ -z "${BUCKET}" ]]
then
	echo "[!] Provide a bucket name as the first parameter"
	exit 1
fi

if [[ -z "${ARTIFACT}" ]]
then
	echo '[!] It seems you have not created a build yet'
	exit 1
fi

KEY=$(basename $ARTIFACT)

export AWS_DEFAULT_REGION="${REGION}"
export AWS_PROFILE=personal
echo '[i] Uploading artifact to s3'
aws s3 cp "${ARTIFACT}" "s3://${BUCKET}/${KEY}"

# @todo update stack 
echo '[i] Creating cloudformation stack'
aws cloudformation create-stack \
  --stack-name zap-lambda \
  --capabilities CAPABILITY_NAMED_IAM \
  --template-body file://cloudformation.json \
  --on-failure ROLLBACK \
  --parameters ParameterKey=S3Bucket,ParameterValue="${BUCKET}" ParameterKey=S3Key,ParameterValue="${KEY}"
