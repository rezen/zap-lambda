#!/bin/sh
hash=$(find ./code/  -type f -exec md5sum {} \; | sort -k 2 | md5sum | cut -d' ' -f1)
printf '{"hash":"%s"}' "${hash}"