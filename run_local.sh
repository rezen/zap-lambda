#!/bin/bash
set -e

if [ ! -d $HOME/.aws ]
then
  echo '[INFO] Creating fake aws key for local dev'
  mkdir -p $HOME/.aws
  echo '[default]' > $HOME/.aws/credentials
  echo 'region=us-west-1' >> $HOME/.aws/credentials
  echo 'aws_access_key_id=XXXXXXXXXXXXXX' >> $HOME/.aws/credentials
  echo 'aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYY' >> $HOME/.aws/credentials
fi

# @todo have a separate container for dynamodb
echo "[INFO] starting dyanmodb in background"
# java -Djava.library.path=. -jar /opt/DynamoDBLocal.jar \
#  -sharedDb \
#  -dbPath /data/dynamodb \
#  -port 8000 &

echo '[INFO] Starting gunicorn'
export PYTHONBUFFERED=1
exec gunicorn -b :5000 app:app \
  --error-logfile - \
  --capture-output \
  --log-level debug
