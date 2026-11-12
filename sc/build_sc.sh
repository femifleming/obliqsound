#!/bin/bash
# Builds the SuperCollider side: OblqUGens.scx, the stock UGen plug-ins, the SynthDefs, and the test tools.
# Needs third_party/supercollider (source, tag Version-3.13.0) built in third_party/sc-build,
# and SuperCollider.app for sclang (to compile the SynthDefs).
set -e
cd "$(dirname "$0")"
SC=../third_party/supercollider; B=../third_party/sc-build
SCLANG=${SCLANG:-/Applications/SuperCollider.app/Contents/MacOS/sclang}
INC="-I$B/common -I$SC/external_libraries -I$SC/external_libraries/nova-simd -I$SC/external_libraries/nova-tt -I$SC/external_libraries/boost -I$SC/include/common -I$SC/common -I$SC/include/server -I$SC/include/plugin_interface -I$SC/server/scsynth -I$SC/external_libraries/boost_sync/include -I$SC/external_libraries/TLSF-2.4.6/src"
DEF="-DBOOST_CHRONO_HEADER_ONLY -DBOOST_CONFIG_SUPPRESS_OUTDATED_MESSAGE -DNOVA_SIMD -DNO_LIBSNDFILE -DSC_FFT_VDSP -DSC_MEMORY_ALIGNMENT=32"
LIBS="$B/server/scsynth/libscsynth.a $B/external_libraries/libtlsf.a $B/external_libraries/libboost_filesystem_lib.a $B/external_libraries/libboost_system_lib.a -framework CoreAudio -framework CoreServices -framework Accelerate -framework Foundation -framework AppKit -framework AudioToolbox"
mkdir -p build/plugins build/defs
# UGens
clang++ -bundle -std=gnu++17 -O3 -DNDEBUG -stdlib=libc++ -arch arm64 -arch x86_64 -mmacosx-version-min=11.0 -fPIC -fvisibility=hidden $DEF $INC ugens/OblqUGens.cpp -o build/plugins/OblqUGens.scx
for p in BinaryOpUGens UnaryOpUGens MulAddUGens IOUGens OscUGens LFUGens NoiseUGens DynNoiseUGens FilterUGens DelayUGens PanUGens TriggerUGens ReverbUGens GrainUGens ChaosUGens DemandUGens PhysicalModelingUGens; do
  cp $B/server/plugins/$p.scx build/plugins/
done
# SynthDefs
printf 'includePaths:\n    - %s/classes\nexcludePaths:\n    []\npostInlineWarnings: false\n' "$PWD" > build/sclang_conf.yaml
rm -f build/defs/*.scsyndef
for f in defs/*.scd; do
  [ "$1" = "tests" ] || case "$f" in *test_*|*spike*) continue;; esac
  "$SCLANG" -l build/sclang_conf.yaml "$f" "$PWD/build/defs" 2>&1 | grep -E "ERROR|rror|WARNING: .*not found" || true
done
# tools
if [ "$1" = "tests" ]; then
  clang++ -std=gnu++17 -O2 -stdlib=libc++ $DEF $INC ugtest.cpp ScEngine.cpp $LIBS -o build/ugtest
  clang++ -std=gnu++17 -O2 -stdlib=libc++ $DEF $INC voicetest.cpp ScEngine.cpp $LIBS -o build/voicetest
fi
echo "sc side built: $(ls build/plugins | wc -l | tr -d ' ') plug-ins, $(ls build/defs | wc -l | tr -d ' ') synthdefs"
