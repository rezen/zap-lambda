#!/bin/bash

set -e

RELEASE="${1:-2018-10-22}"
LABEL='zap-lambda'
BUILD_DIR="./_builds/${RELEASE}"
HERE=$(pwd)

if [ "${#RELEASE}" -ne 10 ]
then
  echo "[!] That is not a valid release input"
  exit 1
fi

rm -rf "${BUILD_DIR}"

echo "[i] Building ZAP in container [release=${RELEASE}]"
docker build --build-arg RELEASE="$RELEASE" . -t $LABEL
container_id=$(docker run --rm --name $LABEL -d $LABEL  sleep 10)

echo '[i] Exporting ZAP assets from container'
docker cp "$container_id:/zap" "${BUILD_DIR}"
touch "${BUILD_DIR}/__init__.py"


echo '[i] Slimming ZAP down'
IFS=$'\n'
remove=(
  accessControl
  diff
  gettingStarted
  help
  jxbrowsermacos
  jxbrowserwindows
  onlineMenu
  portscan
  quickstart
  reveal
  saverawmessage
  savexmlmessage
  sequence
  soap
  tips
  webdrivermacos
  webdriverwindows
  jxbrowser
  jxbrowserlinux64
  invoke
)
for file in "${remove[@]}"
do
	bash -c "rm ${BUILD_DIR}/plugin/${file}-*"
done

echo "[i] Packaging up build"
cd "$BUILD_DIR"
zip -q -r "zap-aws-${RELEASE}.zip" ./*
mv "zap-aws-${RELEASE}.zip" "${HERE}/_builds/"
