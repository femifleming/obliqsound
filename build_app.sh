#!/bin/bash
# Builds the desktop app with its plug-in embedded.
# usage: [NAME=ObliqSound|ObliqSonic] ./build_app.sh [dest dir, default /Applications]
set -e
cd "$(dirname "$0")"
NAME=${NAME:-ObliqSound}
ID=$([ "$NAME" = ObliqSound ] && echo Oblq || echo Oblc)
DEST="${1:-/Applications}"
NAME=$NAME ID=$ID ./build.sh build/$NAME.vst3 >/dev/null
( cd app && cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build --target ${NAME}App >/dev/null )
APP=build/$NAME.app
rm -rf "$APP"; cp -R app/build/${NAME}App_artefacts/Release/$NAME.app "$APP"
mkdir -p "$APP/Contents/PlugIns"; cp -R build/$NAME.vst3 "$APP/Contents/PlugIns/"
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $NAME" "$APP/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $NAME" "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSApplicationCategoryType string public.app-category.music" "$APP/Contents/Info.plist" 2>/dev/null || true
codesign --force --deep -s - "$APP"
rm -rf "$DEST/$NAME.app"; cp -R "$APP" "$DEST/"
echo "built $DEST/$NAME.app"
