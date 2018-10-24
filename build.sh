#!/bin/bash

set -e
RELEASE=2018-10-22
LABEL='zap-serverless'
BUILD_TAG=$(date +%Y%m%d)
BUILD_DIR="./_builds/$RELEASE"
HERE=$(pwd)

rm -rf "$BUILD_DIR"

docker build --build-arg RELEASE="$RELEASE" . -t $LABEL

container_id=$(docker run --rm --name $LABEL -d $LABEL  sleep 10)

docker cp $container_id:/zap "$BUILD_DIR"
touch "$BUILD_DIR/__init__.py"
mv $BUILD_DIR/py/lib/python2.7/site-packages $BUILD_DIR/vendor

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
	bash -c "rm $BUILD_DIR/plugin/$file-*"
done

cd "$BUILD_DIR"

zip -r "zap-aws-${RELEASE}.zip" ./*
mv "zap-aws-${RELEASE}.zip" "$HERE/_builds/"
