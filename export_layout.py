#!/usr/bin/env python3
"""Turns the generated panel (src/<Name>.csd, written by gen.py) into plugin/Resources/<Name>/layout.json
for the JUCE plug-in: every widget with its page, bounds, channel, range and art, plus the swarm's
parameter assignments and the source / destination names of the matrix.
usage: export_layout.py ObliqSound|ObliqSonic"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__)) + '/'
name = sys.argv[1]
csd = open(ROOT + f'src/{name}.csd', encoding='utf-8').read()
cab = csd[csd.index('<Cabbage>'):csd.index('</Cabbage>')]
orc = csd[csd.index('<CsInstruments>'):csd.index('</CsInstruments>')]

def nums(s):
    return [float(x) for x in s.split(',')]

def strs(s):
    return re.findall(r'"([^"]*)"', s)

widgets, page = [], ''
form = {}
for line in cab.split('\n'):
    t = line.strip()
    if not t or t.startswith('//') or t.startswith('<'):
        continue
    if t == '}':
        page = ''
        continue
    kind = t.split(' ')[0].split('(')[0]
    if kind == 'form':
        m = re.search(r'size\(([^)]*)\)', t); form['size'] = [int(v) for v in nums(m.group(1))]
        continue
    w = {'type': kind, 'page': page}
    m = re.search(r'bounds\(([^)]*)\)', t)
    if not m:
        continue
    w['bounds'] = [int(round(v)) for v in nums(m.group(1))]
    for key, pat in (('channel', r'channel\("([^"]*)"\)'), ('file', r'(?<![a-zA-Z])file\("([^"]*)"\)'), ('group', r'radioGroup\("([^"]*)"\)'),
                     ('popup', r'popupText\("([^"]*)"\)'), ('align', r'align\("([^"]*)"\)'), ('mode', r'mode\("([^"]*)"\)'),
                     ('display', r'displayType\("([^"]*)"\)')):
        m = re.search(pat, t)
        if m: w[key] = m.group(1)
    m = re.search(r'range\(([^)]*)\)', t)
    if m: w['range'] = nums(m.group(1))
    m = re.search(r'(?<![a-zA-Z])value\(([-\d.]+)\)', t)
    if m: w['value'] = float(m.group(1))
    m = re.search(r'alpha\(([-\d.]+)\)', t)
    if m: w['alpha'] = float(m.group(1))
    m = re.search(r'visible\((\d)\)', t)
    if m: w['visible'] = int(m.group(1))
    m = re.search(r'filmstrip\("([^"]*)",\s*(\d+)\)', t)
    if m: w['strip'] = m.group(1); w['frames'] = int(m.group(2))
    m = re.search(r'fontColour\(([^)]*)\)', t)
    if m: w['ink'] = [int(v) for v in nums(m.group(1))]
    m = re.search(r'(?<![a-zA-Z:])text\((.*?)\)(?:[, ]|$)', t)
    if m: w['text'] = strs(m.group(1))
    m = re.search(r'signalVariable\(([^)]*)\)', t)
    if m: w['signals'] = strs(m.group(1))
    if 'imgFile("On"' in t:
        w['on'] = re.search(r'imgFile\("On", "([^"]*)"\)', t).group(1); w['off'] = re.search(r'imgFile\("Off", "([^"]*)"\)', t).group(1)
    if 'imgFile("Slider"' in t:
        w['cap'] = re.search(r'imgFile\("Slider", "([^"]*)"\)', t).group(1)
    if kind == 'image' and t.endswith('{'):
        page = w.get('channel', '')
        w['container'] = True
        w['page'] = ''
    if kind == 'combobox' and 'populate(' in t:
        w['presets'] = True
        w.pop('text', None)
    widgets.append(w)

# ---- the swarm: which boid coordinate and Lorenz axis moves which parameter (from the generated orchestra)
gk2ch = dict(re.findall(r'^\s*(gk\w+) chnget "(\w+)"', orc, re.M))
swarm = []
blk = orc[orc.index('; ---- swarm modulation (generated)'):]
blk = blk[:blk.index('kpcnt init 0')]
for ln in blk.split('\n'):
    m = re.match(r'\s*(gk\w+) limit \1 ([+*]) (.*), ([-\d.e]+), ([-\d.e]+)$', ln)
    if not m: continue
    gk, op, expr, lo, hi = m.groups()
    mm = re.search(r'gkSwB\[(\d)\] \* gkBoid([XY])\[(\d)\] \+ gkSwL\[\d\] \* (-?)gkLor([XYZ])\)', expr)
    amt = re.search(r'\) \* ([-\d.e]+)$', expr)
    swarm.append({'ch': gk2ch[gk], 'sec': int(mm.group(1)), 'axis': mm.group(2), 'boid': int(mm.group(3)), 'sign': -1 if mm.group(4) else 1,
                  'lor': mm.group(5), 'mul': op == '*', 'amt': float(amt.group(1)) if (amt and op == '+') else 3.0, 'lo': float(lo), 'hi': float(hi)})

# ---- matrix names (rows = sources, columns = destinations), recovered from the pins' pop-ups
srcs, dsts = {}, {}
for w in widgets:
    m = re.match(r'p(\d+)_(\d+)$', w.get('channel', ''))
    if m and 'popup' in w:
        s, d = w['popup'].split(' > ')
        srcs[int(m.group(1))] = s; dsts[int(m.group(2))] = d

fnorm = re.search(r'giFNorm\[\] fillarray ([^;\n]*)', orc)
out = {'name': name, 'size': form['size'], 'widgets': widgets, 'swarm': swarm,
       'sources': [srcs[k] for k in sorted(srcs)], 'destinations': [dsts[k] for k in sorted(dsts)],
       'files': open(ROOT + 'samples/index.txt').read().split(),
       'fnorm': [float(v) for v in fnorm.group(1).split(',')] if fnorm else []}
d = ROOT + f'plugin/Resources/{name}'
os.makedirs(d, exist_ok=True)
json.dump(out, open(d + '/layout.json', 'w'))
kinds = {}
for w in widgets: kinds[w['type']] = kinds.get(w['type'], 0) + 1
print(name, 'layout:', len(widgets), 'widgets', kinds, '| swarm', len(swarm), '| sources', len(out['sources']), 'destinations', len(out['destinations']))
