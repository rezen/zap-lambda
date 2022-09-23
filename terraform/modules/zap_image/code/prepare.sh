#!/bin/bash

set -e

echo '-- Removing unused plugins'
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
  hud-beta
)
for file in "${remove[@]}"
do
	bash -c "rm -rf /zap/plugin/${file}-*"
done


