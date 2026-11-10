#!/bin/bash
# render presets (full values) via CLI harness: rpre.sh "name" ...
cd "$(dirname "$0")/.."
for n in "$@"; do
  args=$(python3 -c "
import json,sys; d=json.load(open('/Users/Shared/ObliqSound/ObliqSound presets.snaps'))[sys.argv[1]]
print(','.join(f'{k}={v}' for k,v in d.items() if isinstance(v,(int,float)) and not isinstance(v,bool)))" "$n")
  python3 work/dbg.py renders/pre.wav "$args" "48:0.2:1.8,55:0.2:1.8,60:0.2:1.8,64:0.2:1.8,72:2.4:1.2" 4.2 | grep -v "^$" | head -3
  printf "%-32s " "${n:0:32}"; .venv/bin/python work/rms.py renders/pre.wav
done
