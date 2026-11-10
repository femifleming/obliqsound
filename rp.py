# render a preset from the XL snaps through the real plugin
import json, subprocess, sys, os, time
H = os.path.expanduser('~/kia-xl/host/build/KiaHost_artefacts/Release/KiaHost.app/Contents/MacOS/KiaHost')
PLUG = os.path.expanduser(os.environ.get('PLUG', '~/kia-xl/build/Kia_instrument_XL.vst3'))
snaps = json.load(open('/Users/Shared/ObliqSound/ObliqSound presets.snaps'))
import re
CSD = open(os.path.expanduser('~/kia-xl/src/ObliqSound.csd'), encoding='latin-1').read()
RANGES = {}
for line in CSD.split('\n'):
    m = re.search(r'channel\("([^"]+)"\)', line)
    if not m: continue
    ch = m.group(1)
    r = re.search(r'range\(([^)]*)\)', line)
    if r:
        a = [float(x) for x in r.group(1).split(',')]
        RANGES[ch] = (a[0], a[1], a[3] if len(a) > 3 else 1)
    elif line.lstrip().startswith('combobox') and 'text(' in line:
        n = len(re.findall(r'"[^"]*"', line.split('text(')[1].split(')')[0]))
        RANGES[ch] = (1, n, 1)
    else:
        RANGES[ch] = (0, 1, 1)
def norm(ch, v):
    lo, hi, sk = RANGES.get(ch, (0, 1, 1))
    x = min(max((v - lo) / (hi - lo), 0), 1)
    return x ** sk
SKIP = {'form','image6','label8','kia','keyboard142','image120','image71','image72','info','info_box','signaldisplay141',
        'filebutton85','filebutton86','image122','image126','Swave1','Swave2','Swave3','Swave4','combo84','xlShow'}
def render(name, out, notes, secs):
    p = snaps[name]; args = [H, PLUG]
    for k, v in p.items():
        if k in SKIP or k.startswith('Act') or k.startswith('label') or k.endswith('a') and k[:-1] in p: continue
        args += ['--set', f'{k}={norm(k, float(v))}']
    args += ['--wav', out, '--secs', str(secs), '--notes', notes]
    t = time.time(); r = subprocess.run(args, capture_output=True, text=True); dt = time.time() - t
    line = [l for l in r.stdout.splitlines() if l.startswith('render')]
    bad = [l for l in r.stdout.splitlines() if l.startswith('no param')]
    return (line[0] if line else 'NO RENDER') + f'  wall={dt:.1f}s' + (f'  missing={len(bad)}' if bad else '')
if __name__ == '__main__':
    notes = os.environ.get('NOTES', '48:0.3:1.8,55:0.3:1.8,60:0.3:1.8,64:0.3:1.8,72:2.6:1.0')
    for n in sys.argv[1:]:
        out = os.path.expanduser('~/kia-xl/renders/' + n.replace(' ', '_').replace('/', '') + '.wav')
        print(f'{n[:32]:32}', render(n, out, notes, float(os.environ.get('SECS', 5))))
