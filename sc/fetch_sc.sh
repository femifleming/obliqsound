#!/bin/bash
# Fetches SuperCollider 3.13.0 and builds its synthesis server as a static library, with its UGen plug-ins.
# macOS: universal. Linux: needs libjack-jackd2-dev (headers only; JACK is not linked into the plug-ins).
# Windows: run from a shell with MSVC set up (x64) and Ninja.
set -e
cd "$(dirname "$0")/.."
mkdir -p third_party && cd third_party
[ -d supercollider ] || git clone --depth 1 --branch Version-3.13.0 --recurse-submodules --shallow-submodules https://github.com/supercollider/supercollider.git
mkdir -p sc-build && cd sc-build
case "$(uname -s)" in
  Darwin) EXTRA=(-DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0) ;;
  Linux)  EXTRA=(-DFFT_GREEN=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DNO_AVAHI=ON -DSC_USE_QTWEBENGINE=OFF) ;;
  *)      EXTRA=(-DFFT_GREEN=ON -DCMAKE_C_COMPILER=cl -DCMAKE_CXX_COMPILER=cl -DCMAKE_RC_COMPILER=rc) ;;
esac
cmake -G Ninja ../supercollider -DCMAKE_BUILD_TYPE=Release "${EXTRA[@]}" \
  -DSC_QT=OFF -DSC_IDE=OFF -DSUPERNOVA=OFF -DENABLE_TESTSUITE=OFF -DSC_ABLETON_LINK=OFF -DSC_HIDAPI=OFF -DNO_LIBSNDFILE=ON \
  -DSC_EL=OFF -DSC_ED=OFF -DSC_VIM=OFF -DINSTALL_HELP=OFF -DNATIVE=OFF -DNO_X11=ON
ninja libscsynth
[ "$(uname -s)" = Darwin ] || [ "$(uname -s)" = Linux ] || exit 0     # Windows: the UGens are built by plugin/CMakeLists.txt
ninja BinaryOpUGens UnaryOpUGens MulAddUGens IOUGens OscUGens LFUGens NoiseUGens DynNoiseUGens FilterUGens DelayUGens PanUGens TriggerUGens ReverbUGens GrainUGens ChaosUGens DemandUGens PhysicalModelingUGens
