# Render the engine with the csound CLI: widget defaults + overrides, MIDI-like notes via score.
# usage: dbg.py out.wav "chan=val,..." "note:start:dur,..." secs [extra orc code]
import sys, re, os, subprocess
csd = open(os.path.expanduser(os.environ.get('CSD', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'ObliqSound.csd'))), encoding='latin-1').read()
cab = csd[csd.index('<Cabbage>'):csd.index('</Cabbage>')]
defs = {}
for line in cab.split('\n'):
    if line.strip().startswith(';') or line.strip().startswith('//'): continue
    m = re.search(r'channel\("([^"]+)"\)', line)
    if not m: continue
    ch = m.group(1)
    r = re.search(r'range\(([^)]*)\)', line)
    v = re.search(r'value\(([-\d.]+)\)', line)
    if r: defs[ch] = float(r.group(1).split(',')[2])
    elif v: defs[ch] = float(v.group(1))
    elif line.lstrip().startswith(('checkbox', 'combobox', 'button')): defs[ch] = 0.0
for kv in filter(None, sys.argv[2].split(',')):
    k, v = kv.split('='); defs[k] = float(v)
orc = csd[csd.index('<CsInstruments>') + 15:csd.index('</CsInstruments>')]
stub = '''
opcode cabbageSet, 0, kSSkkk
 k1,S1,S2,k2,k3,k4 xin
endop
opcode cabbageSet, 0, kSSkkkk
 k1,S1,S2,k2,k3,k4,k5 xin
endop
opcode cabbageSet, 0, kSSk
 k1,S1,S2,k2 xin
endop
opcode cabbageSet, 0, kSSS
 k1,S1,S2,S3 xin
endop
opcode cabbageSet, 0, SSi
 S1,S2,i1 xin
endop
opcode cabbageSetValue, 0, Skk
 S1,k1,k2 xin
endop
'''
init = '\n'.join(f'chnset {v}, "{k}"' for k, v in defs.items()) + '\nchnset 120, "HOST_BPM"\nchnset "' + os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) + '", "CSD_PATH"\n'
orc = orc.replace('giSine ftgen', stub + init + 'giSine ftgen', 1)
orc = orc.replace('massign 0, 1\n', '')
# score-driven voice: emulate MIDI note via p4/p5
orc = orc.replace('  inote notnum\n  ivel veloc 0, 127\n', '  inote = p4\n  ivel = p5\n')
orc = orc.replace('  krel release\n', '  krel release\n') 
orc = orc.replace('  gkBend pchbend 0, 2\n  gkMWheel midictrl 1, 0, 1\n  gkATouch aftouch 0, 1\n', '')
orc = orc.replace('zdf_2pole_mode', 'zdf2polemode')
orc += '\ninstr 98\n exitnow\nendin\n'
if len(sys.argv) > 5: orc += '\n' + open(sys.argv[5]).read()
open('dbg.orc', 'w').write(orc)
sco = ''.join(f'i1 {n.split(":")[1]} {n.split(":")[2]} {n.split(":")[0]} 100\n' for n in filter(None, sys.argv[3].split(',')))
sco += f'i 98 {float(sys.argv[4]) - 0.01} 0.1\ne {sys.argv[4]}\n'
open('dbg.sco', 'w').write(sco)
r = subprocess.run(['csound', '-d', '-m0', '--sample-rate=48000', '-W', '-f', '-o', sys.argv[1], 'dbg.orc', 'dbg.sco'],
                   capture_output=True, text=True, timeout=300)
for l in (r.stdout + r.stderr).split('\n'):
    if re.search(r'error|ERROR|DBG|unexpected', l): print(l)
