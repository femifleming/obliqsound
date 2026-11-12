#!/bin/bash
# Fills a built bundle's Contents/Resources with everything the plug-in loads at run time.
# usage: copy_resources.sh ObliqSound|ObliqSonic <bundle path (.vst3 / .component / .app)>
set -e
NAME=$1; BUNDLE=$2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
R="$BUNDLE/Contents/Resources"
PFX=$([ "$NAME" = ObliqSonic ] && echo sx || echo "")
mkdir -p "$R/plugins" "$R/defs" "$R/samples" "$R/art"
cp "$ROOT"/sc/build/plugins/*.scx "$R/plugins/"
cp "$ROOT"/sc/build/defs/o*.scsyndef "$R/defs/"
cp "$ROOT"/samples/*.wav "$ROOT"/samples/index.txt "$R/samples/"
cp "$ROOT/plugin/Resources/$NAME/layout.json" "$R/layout.json"
cp "$ROOT/manual/ObliqSound_ObliqSonic_Manual.pdf" "$R/"
cp "/Users/Shared/$NAME/$NAME presets.snaps" "$R/presets.json"
# art: every file the layout names, the landscape frames, the read-out images, the font
python3 - "$ROOT" "$R" "$NAME" "$PFX" <<'PY'
import json, sys, shutil, glob, os
root, r, name, pfx = sys.argv[1:5]
lay = json.load(open(r + '/layout.json'))
files = set()
for w in lay['widgets']:
    for k in ('file', 'strip', 'on', 'off', 'cap'):
        if w.get(k) and not w[k].startswith(pfx + 'bg_'): files.add(w[k])
for f in files:
    if os.path.exists(root + '/src/' + f): shutil.copy(root + '/src/' + f, r + '/art/' + f)
for pat in (pfx + 'bg_*.png', pfx + 'lcd_*.png'):
    for f in glob.glob(root + '/src/' + pat): shutil.copy(f, r + '/art/')
shutil.copy(root + '/src/Tahoma Bold.ttf', r + '/art/')
PY
codesign --force --deep -s - "$BUNDLE" 2>/dev/null || true
echo "resources -> $BUNDLE ($(du -sh "$R" | cut -f1))"
