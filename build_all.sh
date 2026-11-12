#!/bin/bash
# Builds ObliqSound and ObliqSonic (VST3, Audio Unit, desktop app) and zips them into dist/.
# First time only: sc/fetch_sc.sh (fetches and builds SuperCollider's server). Needs SuperCollider.app for sclang,
# a JUCE checkout (JUCE_DIR), CMake, Ninja, and Python with numpy, scipy, Pillow.
set -e
cd "$(dirname "$0")"
[ -f third_party/sc-build/server/scsynth/libscsynth.a ] || sc/fetch_sc.sh
sc/build_sc.sh
for N in ObliqSound ObliqSonic; do
  mkdir -p "/Users/Shared/$N"
  .venv/bin/python gen.py src/$N.csd > /dev/null          # panel art, layout source, presets
  .venv/bin/python export_layout.py $N
done
.venv/bin/python manual/mkmanual.py > /dev/null && .venv/bin/python manual/mklog.py > /dev/null    # the manual goes inside the bundles
cmake -S plugin -B plugin/build -G Ninja -DCMAKE_BUILD_TYPE=Release > /dev/null
cmake --build plugin/build > plugin/build.log
mkdir -p dist && find dist -name "*.zip" -delete
for N in ObliqSound ObliqSonic; do
  A=plugin/build/${N}_artefacts/Release
  for pair in "VST3/$N.vst3:VST3" "AU/$N.component:AU" "Standalone/$N.app:App"; do
    B="$A/${pair%%:*}"; K="${pair##*:}"
    plugin/copy_resources.sh $N "$PWD/$B" > /dev/null
    ditto -c -k --norsrc --noextattr --keepParent "$B" "dist/$N-$K-macOS.zip"
  done
done
cp manual/ObliqSound_ObliqSonic_Manual.pdf manual/ObliqSound_Request_Log.pdf dist/
ls -la dist
