#!/bin/bash
# syntax/run check of the engine with the csound CLI (cabbage opcodes stubbed)
cd ~/kia-xl && python3 gen.py src/Kia_instrument_XL.csd >/dev/null && cd work && python3 - <<'PY'
import os
csd=open(os.path.expanduser('~/kia-xl/src/Kia_instrument_XL.csd'),encoding='latin-1').read()
orc=csd[csd.index('<CsInstruments>')+15:csd.index('</CsInstruments>')]
stub='''
opcode cabbageSet, 0, kSSkkk
 k1,S1,S2,k2,k3,k4 xin
endop
opcode cabbageSet, 0, kSSk
 k1,S1,S2,k2 xin
endop
opcode cabbageSet, 0, kSSS
 k1,S1,S2,S3 xin
endop
opcode cabbageSetValue, 0, Skk
 S1,k1,k2 xin
endop
'''
orc=orc.replace('giSine ftgen', stub+'giSine ftgen',1)
orc=orc.replace('Sdir chnget "CSD_PATH"','Sdir = "/Users/femishonugafleming/kia-xl"')
open('check.orc','w').write(orc)
PY
csound -n -d -m0 --sample-rate=48000 check.orc ${1:-check.sco} 2>&1 | grep -iE "error|unexpected|not found|INIT ERROR|PERF ERROR|line [0-9]+" | head -${2:-15}
