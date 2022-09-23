#!/bin/bash
set -e

echo "[INFO] This is pid $pid"
mkdir -p /tmp/sls/

if [ ! -d $HOME/.aws ]
then
  echo '[INFO] Creating fake aws key for local dev'
  mkdir -p $HOME/.aws
  echo '[default]' > $HOME/.aws/credentials
  echo 'aws_access_key_id=XXXXXXXXXXXXXX' >> $HOME/.aws/credentials
  echo 'aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYY' >> $HOME/.aws/credentials
fi

export AWS_BUCKET=test 
export IS_LOCAL=1

moto_server s3 -p8006 > /tmp/sls/s3.log 2>&1 &
echo "[INFO] Started local test"
python zap_lambda.py --test
