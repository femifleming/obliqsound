#!/bin/bash
# Assemble ObliqSound.vst (VST2) from the original Cabbage VST2 shell + the same csd/assets as the VST3.
set -e
cd "$(dirname "$0")"
NAME=${NAME:-ObliqSound}            # ObliqSound | ObliqSonic
ID=${ID:-Oblq}                      # 4-char plug-in id: Oblq | Oblc
LOW=$([ "$NAME" = ObliqSound ] && echo synth || echo sonic)
OUT=${1:-build/$NAME.vst}
.venv/bin/python gen.py src/$NAME.csd >/dev/null
rm -rf "$OUT"; mkdir -p "$(dirname "$OUT")"
cp -R original-backup/Kia_instrument.vst "$OUT"
C="$OUT/Contents"
mv "$C/MacOS/Kia_instrument" "$C/MacOS/$NAME"
rm -f "$C/Kia_instrument.csd"
cp src/$NAME.csd "$C/"
for f in $(LC_ALL=C sed -n "/<CabbageIncludes>/,/<\/CabbageIncludes>/p" src/$NAME.csd | grep png); do cp "src/$f" "$C/"; done
cp src/*.ttf "$C/" 2>/dev/null || true
mkdir -p "$C/samples" && cp samples/*.wav "$C/samples/"
# VST2 unique ID + version live in __TEXT,__const as "move" + version (one per arch) -> "Oblq"
ID=$ID python3 - "$C/MacOS/$NAME" <<'PY'
import sys, os
p = sys.argv[1]; b = open(p, 'rb').read()
pat = b'movek\x08\x02\x00'
n = b.count(pat); assert n == 2, n
open(p, 'wb').write(b.replace(pat, os.environ['ID'].encode() + b'k\x08\x02\x00'))
PY
for k in CFBundleExecutable CFBundleName CFBundleDisplayName; do
  plutil -replace $k -string $NAME "$C/Info.plist"; done
plutil -replace CFBundleIdentifier -string com.obliqsound.$LOW.vst2 "$C/Info.plist"
codesign --force --deep -s - "$OUT" 2>/dev/null
echo "built $OUT"
