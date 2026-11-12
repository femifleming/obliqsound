#!/bin/bash
# Fetches SuperCollider 3.13.0 and builds its synthesis server as a universal static library, with its UGen plug-ins.
set -e
cd "$(dirname "$0")/.."
mkdir -p third_party && cd third_party
[ -d supercollider ] || git clone --depth 1 --branch Version-3.13.0 --recurse-submodules --shallow-submodules https://github.com/supercollider/supercollider.git
mkdir -p sc-build && cd sc-build
cmake -G Ninja ../supercollider -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
  -DSC_QT=OFF -DSC_IDE=OFF -DSUPERNOVA=OFF -DENABLE_TESTSUITE=OFF -DSC_ABLETON_LINK=OFF -DSC_HIDAPI=OFF -DNO_LIBSNDFILE=ON \
  -DSC_EL=OFF -DSC_ED=OFF -DSC_VIM=OFF -DINSTALL_HELP=OFF -DNATIVE=OFF -DNO_X11=ON
ninja libscsynth
ninja server/plugins/all
