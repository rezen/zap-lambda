#!/bin/bash

set -e

echo "-- Pushing ecr container"
aws ecr get-login-password  --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin "${ECR_HOST}"
docker build  -t "${ZAP_DOCKER_IMAGE}"  . -f Dockerfile
docker tag "${ZAP_DOCKER_IMAGE}" "${ECR_HOST}/${IMAGE_PATH}"
docker push "${ECR_HOST}/${IMAGE_PATH}"
digest=$(docker inspect "${ZAP_DOCKER_IMAGE}" --format "{{ index .RepoDigests 0 }}")

printf '{"repo":"%s"}' "${digest}" > image_data.json
echo '-- Finished pushing ecr image'
echo "   ${ECR_HOST}/${IMAGE_PATH}"