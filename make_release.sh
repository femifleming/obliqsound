#!/bin/bash
# Builds every deliverable and zips them into dist/ for a GitHub release.
set -e
cd "$(dirname "$0")"
rm -rf dist; mkdir -p dist
rm -rf app/build
for N in ObliqSound ObliqSonic; do
  I=$([ $N = ObliqSound ] && echo Oblq || echo Oblc)
  NAME=$N ID=$I ./build.sh build/$N.vst3 >/dev/null
  NAME=$N ID=$I ./build_vst2.sh build/$N.vst >/dev/null
  NAME=$N ./build_app.sh build/apps >/dev/null 2>&1 || { mkdir -p build/apps; NAME=$N ./build_app.sh build/apps; }
  ( cd build && ditto -c -k --norsrc --noextattr --keepParent $N.vst3 ../dist/$N-VST3-macOS.zip && ditto -c -k --norsrc --noextattr --keepParent $N.vst ../dist/$N-VST2-macOS.zip )
  ( cd build/apps && ditto -c -k --norsrc --noextattr --keepParent $N.app ../../dist/$N-App-macOS.zip )
done
cp manual/ObliqSound_ObliqSonic_Manual.pdf dist/
ls -la dist
