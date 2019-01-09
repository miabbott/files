#!/usr/bin/env bash

JQ_VERSION="1.6"

ctr=$(buildah from scratch)

mp=$(buildah mount $ctr)

mkdir -p $mp/usr/bin
wget --no-check-certificate https://raw.githubusercontent.com/stedolan/jq/master/sig/jq-release.key -O /tmp/jq-release.key
wget --no-check-certificate https://raw.githubusercontent.com/stedolan/jq/master/sig/v${JQ_VERSION}/jq-linux64.asc -O /tmp/jq-linux64.asc
wget --no-check-certificate https://github.com/stedolan/jq/releases/download/jq-${JQ_VERSION}/jq-linux64 -O /tmp/jq-linux64
gpg --import /tmp/jq-release.key
gpg --verify /tmp/jq-linux64.asc /tmp/jq-linux64
cp /tmp/jq-linux64 $mp/usr/bin/jq
chmod +x $mp/usr/bin/jq
rm -f /tmp/jq-release.key
rm -f /tmp/jq-linux64.asc
rm -f /tmp/jq-linux64

buildah config --entrypoint '["/usr/bin/jq"]' $ctr

buildah commit $ctr miabbott/jq

buildah unmount $ctr
buildah rm $ctr
