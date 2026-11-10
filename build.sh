#!/bin/bash
# Assemble ObliqSound.vst3 from the original Cabbage shell + our csd.
set -e
cd "$(dirname "$0")"
NAME=${NAME:-ObliqSound}            # ObliqSound | ObliqSonic
ID=${ID:-Oblq}                      # 4-char plug-in id: Oblq | Oblc
LOW=$([ "$NAME" = ObliqSound ] && echo synth || echo sonic)
OUT=${1:-build/$NAME.vst3}
mkdir -p "/Users/Shared/$NAME"
.venv/bin/python gen.py src/$NAME.csd >/dev/null
rm -rf "$OUT"; mkdir -p "$(dirname "$OUT")"
cp -R original-backup/Kia_instrument.vst3 "$OUT"
C="$OUT/Contents"
mv "$C/MacOS/Kia_instrument" "$C/MacOS/$NAME"
rm -f "$C/Kia_instrument.csd"
cp src/$NAME.csd "$C/"
for f in $(LC_ALL=C sed -n "/<CabbageIncludes>/,/<\/CabbageIncludes>/p" src/$NAME.csd | grep png); do cp "src/$f" "$C/"; done
cp src/*.ttf "$C/" 2>/dev/null || true
mkdir -p "$C/samples" && cp samples/*.wav "$C/samples/"
# new VST3 class IDs so it lives next to the original (Aufbmove -> AufbOblq)
ID=$ID python3 - "$C/MacOS/$NAME" <<'PY'
import sys, os
p = sys.argv[1]; b = open(p, 'rb').read()
n = b.count(b'Aufbmove'); assert n == 6, n
open(p, 'wb').write(b.replace(b'Aufbmove', b'Aufb' + os.environ['ID'].encode()))
PY
for k in CFBundleExecutable CFBundleName CFBundleDisplayName; do
  plutil -replace $k -string $NAME "$C/Info.plist"; done
plutil -replace CFBundleIdentifier -string com.obliqsound.$LOW "$C/Info.plist"
codesign --force --deep -s - "$OUT" 2>/dev/null
echo "built $OUT"
