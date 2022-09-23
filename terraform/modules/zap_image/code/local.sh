#!/bin/bash

set -e


function cleanup()
{
    '-- Cleanup'
    docker kill "${docker_id}"
    echo
}

trap cleanup SIGINT


exposed_port=9113
docker build -t zap-lambda .
docker_id=$(docker run -d -v ~/.aws-lambda-rie:/aws-lambda -p "${exposed_port}:8080" \
    --entrypoint /aws-lambda/aws-lambda-rie \
    zap-lambda:latest \
        /usr/bin/python -m awslambdaric app.handler)

echo '-- Sleeping ...'
sleep 3

curl -XPOST "http://localhost:${exposed_port}/2015-03-31/functions/function/invocations" -d '{}'
echo 
docker kill "${docker_id}"
