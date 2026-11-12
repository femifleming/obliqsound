#!/bin/bash
# Windows / Linux: fills the built VST3 bundles and desktop apps with the resources and zips them into dist/.
# The platform-independent resources (art, layout, presets, SynthDefs, recordings, manual) are taken from the
# macOS VST3 zips of a release, which gen.py and sclang produced on the Mac.
# usage: ci/package.sh <Windows|Linux> <folder holding ObliqSound-VST3-macOS.zip and ObliqSonic-VST3-macOS.zip> [build dir]
set -e
OS=$1; MAC=$2; B=${3:-plugin/build}
cd "$(dirname "$0")/.."
SCP=third_party/sc-build/server/plugins
EXT=$([ "$OS" = Linux ] && echo so || echo scx)
rm -rf dist ci/tmp && mkdir -p dist ci/tmp
zipdir() { if command -v zip >/dev/null; then zip -q -r "$1" "$2"; else 7z a -tzip -bso0 -bsp0 "$1" "$2"; fi; }   # zipdir <zip> <folder>
for N in ObliqSound ObliqSonic; do
  if command -v 7z >/dev/null; then 7z x -y -bso0 -bsp0 "$MAC/$N-VST3-macOS.zip" -oci/tmp; else unzip -q -o "$MAC/$N-VST3-macOS.zip" -d ci/tmp; fi
  SRC=ci/tmp/$N.vst3/Contents/Resources
  [ -f "$SRC/layout.json" ] && [ -d "$SRC/defs" ] && [ -d "$SRC/art" ] || { echo "resources missing in $MAC/$N-VST3-macOS.zip"; exit 1; }
  rm -rf "$SRC/plugins" && mkdir -p "$SRC/plugins"
  for p in BinaryOpUGens UnaryOpUGens MulAddUGens IOUGens OscUGens LFUGens NoiseUGens DynNoiseUGens FilterUGens DelayUGens PanUGens TriggerUGens ReverbUGens GrainUGens ChaosUGens DemandUGens PhysicalModelingUGens; do
    cp "$(find $SCP $B/scplugins -name "$p.$EXT" 2>/dev/null | head -1)" "$SRC/plugins/"
  done
  cp "$(find $B -maxdepth 2 -name "OblqUGens.$EXT" | head -1)" "$SRC/plugins/"
  # VST3
  V=$(find $B/${N}_artefacts -type d -name "$N.vst3" | head -1)
  mkdir -p "$V/Contents/Resources" && cp -R "$SRC"/. "$V/Contents/Resources/"
  (cd "$(dirname "$V")" && zipdir "$OLDPWD/dist/$N-VST3-$OS.zip" "$N.vst3")
  # desktop app: the program with its Resources folder beside it
  A=ci/tmp/app/$N; mkdir -p "$A"
  cp "$(find $B/${N}_artefacts -path "*Standalone*" -type f \( -name "$N" -o -name "$N.exe" \) | head -1)" "$A/"
  cp -R "$SRC" "$A/Resources"
  (cd ci/tmp/app && zipdir "$OLDPWD/dist/$N-App-$OS.zip" "$N")
done
ls -la dist
