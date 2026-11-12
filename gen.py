#!/usr/bin/env python3
"""ObliqSound / ObliqSonic - panel, engine and preset generator.
Every element is placed either ON the centre line or as an exact MIRROR PAIR,
the brushed-aluminium panel (with tick scales under every knob) is rendered to
match, a symmetry check runs before writing, and the engine orc is completed."""
import json, os, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HOME = os.path.expanduser('~')
ROOT = os.path.dirname(os.path.abspath(__file__)) + '/'
SNAPS_ORIG = ROOT + 'presets/base.snaps'
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT + 'src/ObliqSound.csd'
SONIC = 'sonic' in os.path.basename(OUT).lower()          # ObliqSonic: the 16-channel ambisonic encoder version
NAME = 'ObliqSonic' if SONIC else 'ObliqSound'
PFX = 'sx' if SONIC else ''                                # generated art of the two products must not collide in src/
SNAPS_XL = f'/Users/Shared/{NAME}/{NAME} presets.snaps'
os.makedirs(os.path.dirname(SNAPS_XL), exist_ok=True)
FILES = open(ROOT + 'samples/index.txt').read().split()
W, H = 960, 630
AX = W / 2
KS = {'L': 60, 'M': 42, 'S': 32, 'X': 24}               # knob sizes
STRIP = {'L': 'knob_big.png', 'M': 'knob_med.png', 'S': 'knob_small.png', 'X': 'knob_small.png'}
INK = 'fontColour(8, 22, 14, 255)'
INK2 = 'fontColour(30, 60, 42, 255)'
TITLE = 'fontColour(8, 22, 14, 255)'
LCD2 = 'fontColour(150, 255, 175, 255)'
COMBO = 'colour(255, 255, 255, 255) outlineColour(0, 0, 0, 255) fontColour(0, 0, 0, 255)'

SRC = ['none', 'LFO 1', 'LFO 2', 'Mod Env', 'Amp Env', 'Velocity', 'Key', 'Mod Wheel', 'Aftertouch', 'Random',
       'Chaos', 'Nature', 'Follower', 'Output', 'Boid X', 'Boid Y', 'Lorenz X', 'Lorenz Y', 'Lorenz Z',
       'CC A', 'CC B', 'CC C', 'CC D']
CC_DEFAULT = [74, 71, 21, 22]                              # what the four CC rows listen to until you change them
DST = ['none', 'Pitch', 'Cutoff', 'Resonance', 'Pulse Width', 'Fold', 'FM', 'Sub', 'Noise',
       'Resonate', 'Detune', 'Amp', 'Pan', 'LFO 1 Rate', 'LFO 2 Rate', 'Delay', 'Reverb',
       'Poly Order', 'Poly Teeth', 'Poly Roll', 'Poly OP Amt', 'Poly Level', 'Poly Fold',
       'Ode Partials', 'Ode Tilt', 'Ode Tension', 'Ode Density', 'Ode Warp', 'Ode Peaking', 'Ode Level',
       'Field Pos', 'Field Size', 'Field Level', 'B Cutoff', 'Lester Mode', 'Lester Mix', 'Lester Gain']
if SONIC:
    DST += ['Space Dist', 'Space Azim', 'Space Elev', 'Space Spread', 'Space Dev', 'Space Air']
NATURE = ['wind', 'birds', 'beach', 'geiser', 'forest', 'water', 'thunder', 'night']
SHORT = {'recording_oct25': 'rec', 'Tent_Talk': 'tent1', 'Tent_Talk2': 'tent2', 'Tent_Talk3': 'tent3',
         'baserecording1': 'base', 'embodied_listening': 'body', 'hydrophoneSTEREO': 'hydS',
         'hydrophone': 'hyd1', 'hydrophone2': 'hyd2', 'hydrophone3': 'hyd3', 'oneofthebitches': 'bitch',
         'rivergreenfield': 'river', 'show_sample': 'show', 'sploshes': 'splsh', 'waterandrocks': 'rocks',
         'wingie_drone': 'wing1', 'wingie_drone2': 'wing2', 'wingie_into_norns': 'norns'}

P = {}          # channel -> default
RANGE = {}      # channel -> (lo, hi, skew, section)   (for the swarm modulation)
EL = []         # every placed element (global coords) for the symmetry check + panel art
PAGES = {}      # page name -> list of cabbage lines
cur_page = None
POX, POY, PW, PH = 30, 398, 900, 226      # tab page area
MOX, MOY, MW, MH = 14, 40, 932, 590        # matrix board (covers the panel)

def bowl(cx):
    u = (cx - PW / 2) / (PW / 2)
    return round(8 + 12 * u * u)

def origin(pg):
    return (MOX, MOY) if pg == 'matpanel' else (POX, POY)

def put(line, kind, x, y, w, h, mirror=True):
    if cur_page and cur_page != 'matpanel':
        dy = bowl(x + w / 2)
        line = line.replace(f'bounds({x}, {y},', f'bounds({x}, {y + dy},', 1)
        y = y + dy
    gx, gy = (x + origin(cur_page)[0], y + origin(cur_page)[1]) if cur_page else (x, y)
    EL.append(dict(kind=kind, x=gx, y=gy, w=w, h=h, page=cur_page, mirror=mirror))
    (PAGES.setdefault(cur_page, []) if cur_page else MAIN).append(line)

MAIN = []
def axis():
    return (MW / 2 if cur_page == 'matpanel' else PW / 2) if cur_page else AX
def mx(x, w):           # mirrored x of a box
    return 2 * axis() - x - w

def label(t, cx, y, w=60, h=10, ink=INK, ch=None, mirror=True):
    c = f', channel("{ch}")' if ch else ''
    x = round(cx - w / 2)
    put(f'label bounds({x}, {y}, {w}, {h}), text("{t}"), align("centre"), {ink}{c}', 'label', x, y, w, h, mirror)

def knob(ch, size, cx, y, lo, hi, d, skew=1, inc=0.001, lab=None, sec=None, lw=64):
    w = KS[size]; x = round(cx - w / 2)
    P[ch] = d
    if sec: RANGE[ch] = (lo, hi, skew, sec)
    put(f'rslider bounds({x}, {y}, {w}, {w}), channel("{ch}"), range({lo}, {hi}, {d}, {skew}, {inc}), '
        f'filmstrip("{STRIP[size]}", 64)', 'knob' + size, x, y, w, w)
    if lab is not None:
        label(lab, cx, y + w + 1, lw)

def pair(left, right, x_left_cx, *a, **k):
    """place `left` spec at centre x, and `right` at the mirrored centre"""
    left(x_left_cx, *a, **k)
    right(2 * axis() - x_left_cx, *a, **k)

def ledbtn(ch, cx, y, d=0, group=None, lab=None, size=14, lw=56, popup=None):
    x = round(cx - size / 2); h = size
    P[ch] = d
    g = f' radioGroup("{group}")' if group else ''
    pp = f', popupText("{popup}")' if popup else ''
    put(f'checkbox bounds({x}, {y}, {size}, {h}), channel("{ch}"), value({d}){g}, imgFile("On", "btn_on.png"), '
        f'imgFile("Off", "btn_off.png"), colour:0(0, 0, 0, 0), colour:1(0, 0, 0, 0){pp}', 'btn', x, y, size, h)
    if lab is not None:
        label(lab, cx, y + h + 1, lw, 9)

def toggle(ch, cx, y, d=0, lab=None):
    x = round(cx - 16)
    P[ch] = d
    put(f'checkbox bounds({x}, {y}, 32, 18), channel("{ch}"), value({d}), imgFile("On", "sw_on.png"), '
        'imgFile("Off", "sw_off.png"), colour:0(0, 0, 0, 0), colour:1(0, 0, 0, 0)', 'toggle', x, y, 32, 18)
    if lab is not None:
        label(lab, cx, y + 19, 56, 9)

def combo(ch, cx, y, w, items, d, h=16):
    x = round(cx - w / 2)
    P[ch] = d
    t = ', '.join(f'"{i}"' for i in items)
    put(f'combobox bounds({x}, {y}, {w}, {h}), channel("{ch}"), text({t}), value({d}), {COMBO}', 'combo', x, y, w, h)

def vslider(ch, cx, y, h, lo, hi, d, skew=1, sec=None):
    x = round(cx - 10)
    P[ch] = d
    if sec: RANGE[ch] = (lo, hi, skew, sec)
    put(f'vslider bounds({x}, {y}, 20, {h}), channel("{ch}"), range({lo}, {hi}, {d}, {skew}, 0.001), '
        'imgFile("Slider", "slider_cap.png"), trackerColour(0, 0, 0, 0), colour(0, 0, 0, 0), outlineColour(20, 20, 20, 255), '
        'trackerBackgroundColour(20, 20, 20, 255)', 'vslider', x, y, 20, h)

def screen(x, y, w, h):
    dy = bowl(x + w / 2) if cur_page and cur_page != 'matpanel' else 0
    ox, oy = origin(cur_page) if cur_page else (0, 0)
    EL.append(dict(kind='screen', x=x + ox, y=y + dy + oy, w=w, h=h, page=cur_page, mirror=True))

def frame(x, y, w, h, title=None):
    EL.append(dict(kind='frame', x=x + (POX if cur_page else 0), y=y + (POY if cur_page else 0), w=w, h=h, page=cur_page, mirror=True))
    if title:
        label(title, x + w / 2, y + 3, 120, 11)

def image(ch, fn, x, y, w, h, extra='', mirror=True):
    put(f'image bounds({x}, {y}, {w}, {h}), file("{fn}"), channel("{ch}"){extra}', 'image', x, y, w, h, mirror)

# =========================================================================== HEADER (win2000 controls around the chrome emblem)
def box(x, y, w, h, title=None, kind='box'):
    EL.append(dict(kind=kind, x=x + (POX if cur_page else 0), y=y + (POY if cur_page else 0), w=w, h=h, page=cur_page, mirror=True, title=title))

MAIN.append('@PRESETS@')
MAIN.append(f'filebutton bounds({W - 300}, 15, 52, 18), populate("{SNAPS_XL}", "test"), text("Save", "Save"), mode("named preset") '
            'channel("filebutton85") colour:0(200, 204, 200, 255) colour:1(200, 204, 200, 255) fontColour:0(0, 0, 0, 255) outlineColour(0, 0, 0, 255)')
MAIN.append(f'filebutton bounds({W - 244}, 15, 60, 18), populate("{SNAPS_XL}", "test"), text("Remove", "Remove"), mode("remove preset") '
            'channel("filebutton86") colour:0(200, 204, 200, 255) colour:1(200, 204, 200, 255) fontColour:0(0, 0, 0, 255) outlineColour(0, 0, 0, 255)')
P['rndAll'] = 0
MAIN.append(f'button bounds({W - 180}, 15, 74, 18), channel("rndAll"), text("Randomize", "Randomize"), colour:0(200, 204, 200, 255), '
            'colour:1(200, 204, 200, 255), fontColour:0(0, 0, 0, 255), fontColour:1(0, 90, 30, 255), outlineColour(0, 0, 0, 255), automatable(0)')
MAIN.append(f'combobox bounds({W - 102}, 15, 62, 18), mode("resize"), value(3) channel("PluginResizerCombBox") {COMBO}')
EL.append(dict(kind='emblem', x=round(AX - 92), y=6, w=184, h=36, page=None, mirror=True))

# =========================================================================== MAIN PANEL (organic, mirrored)
def kc(ch, size, cx, cy, lo, hi, d, skew=1, inc=0.001, lab=None, sec=None, lw=56):
    """knob placed by its centre"""
    knob(ch, size, cx, round(cy - KS[size] / 2), lo, hi, d, skew, inc, lab, sec, lw)

def wings(fn):
    """call fn(side) for the left (A) and right (B) wing; fn receives X(cx) mirror helper"""
    for A in (True, False):
        fn(A, (lambda cx: cx) if A else (lambda cx: W - cx))

def polar(c, r, deg):
    a = math.radians(deg)
    return c[0] + r * math.cos(a), c[1] + r * math.sin(a)

GROUPS = []   # (name, [(x, y)]) for membrane seeding is derived from EL automatically

# ---- spine: VCO
kc('VCO', 'L', AX, 86, -15.674, 48, 0, 0.5, 0.1, 'PITCH', 'source', 50)
kc('Tune1', 'S', AX - 70, 112, 1, 1.666, 1, 1, 0.01, 'FINE', 'source', 44)
kc('pw', 'S', AX + 70, 112, 0.01, 0.99, 0.5, 1, 0.01, 'P.WIDTH', 'source', 44)
kc('waveform', 'M', AX, 160, 1, 4, 3, 1, 1, 'WAVE', None, 40)
kc('detune', 'S', AX - 128, 112, 0, 1, 0.18, 1, 0.001, 'DETUNE', 'motion', 44)
kc('vib', 'S', AX + 128, 112, 0, 1, 0, 1, 0.001, 'VIBRATO', 'motion', 44)
def wave_icon(fn, kind):                                   # our own waveform icons, drawn at 2x in the panel ink
    im_ = Image.new('RGBA', (44, 22), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im_)
    if kind == 'sine':
        pts = [(2 + i, 11 - 8 * math.sin(2 * math.pi * 2 * i / 40)) for i in range(41)]
    elif kind == 'tri':
        pts = [(2, 11), (7, 3), (17, 19), (27, 3), (37, 19), (42, 11)]
    elif kind == 'saw':
        pts = [(2, 19), (22, 3), (22, 19), (42, 3), (42, 19)]
    else:
        pts = [(2, 19), (2, 3), (12, 3), (12, 19), (22, 19), (22, 3), (32, 3), (32, 19), (42, 19), (42, 3)]
    d_.line(pts, fill=(8, 22, 14, 255), width=3, joint='curve')
    im_.save(ROOT + 'src/' + fn)
for ch, fn, kind, dx, y in [('Swave3', 'wv_square.png', 'square', -34, 145), ('Swave2', 'wv_saw.png', 'saw', 34, 145),
                            ('Swave4', 'wv_tri.png', 'tri', -34, 170), ('Swave1', 'wv_sine.png', 'sine', 34, 170)]:
    wave_icon(fn, kind)
    image(ch, fn, round(AX + dx - 11), y, 22, 11, ', visible(0)' if ch != 'Swave2' else '')
for ch, dx, t, d in [('OctDn', -24, '-1', 1), ('Oct0', 0, '0', 0), ('OctUp', 24, '+1', 0)]:
    ledbtn(ch, AX + dx, 198, d, '104', t, 12, 22)

# ---- spine: sampler fan (three arcs around the pitch knob)
def ethiopic(n):                   # Ge'ez numerals (1-99)
    ones = ' ፩፪፫፬፭፮፯፰፱'; tens = ' ፲፳፴፵፶፷፸፹፺'
    return (tens[n // 10] if n >= 10 else '') + (ones[n % 10] if n % 10 else '')
names = [ethiopic(i + 1) for i in range(len(NATURE) + len(FILES))]
arcs = [(names[0:8], 146), (names[8:17], 186), (names[17:26], 226)]
k = 0
for row, r in arcs:
    n = len(row); step = math.degrees(36 / r)
    for j, nm in enumerate(row):
        k += 1
        a = 90 - (j - (n - 1) / 2) * step
        x, y = polar((AX, 92), r, a)
        ledbtn(f'S{k}', x, round(y - 7), 1 if k == 1 else 0, '100', None, 14)
        image(f'sl{k}', f'eth_{k}.png', round(x - 16), round(y + 8), 32, 12, ', alpha(0.55)', mirror=False)
box(round(AX - 100), 336, 200, 16, None, 'screen')
put(f'image bounds({round(AX - 96)}, 338, 192, 12), file("{PFX}lcd_1.png"), channel("lcdText")', 'disp', round(AX - 96), 338, 192, 12, False)

# ---- wings
def wing(A, X):
    C = (130, 124)
    kc('LPFreq' if A else 'bCut', 'L', X(C[0]), C[1], 35 if A else 20, 18000, 6548 if A else 18000, 1 if A else 0.25, 1,
       'CUTOFF A' if A else 'CUTOFF B', 'filter', 64)
    for (ch, size, deg, lo, hi, d, lab) in [
            ('Res' if A else 'bRes', 'M', -66, 0, 0.99 if A else 1, 0.12, 'RES'),
            ('aMode' if A else 'bMode', 'M', 5, 0, 4, 0, 'MODE'),
            ('aGain' if A else 'bGain', 'S', 62, 0, 1, 0.5, 'DRIVE'),
            ('mod' if A else 'VCAinit', 'S', 105, 0, 1, 1 if A else 0, 'ENV AMT' if A else 'VCA INIT')]:
        x, y = polar(C, 72 if deg < 0 else 68, deg)
        kc(ch, size, X(round(x)), round(y), lo, hi, d, 1, 0.001, lab, 'filter', 44)
    label('FILTER A' if A else 'FILTER B', X(52), 92, 70, 10, INK2)
    chans = ['FAtt', 'FDec', 'FSus', 'FRel'] if A else ['AAtt', 'ADec', 'ASus', 'ARel']
    rng = ([(0.01, 1, 0.11, 1), (0, 1, 0.34, 1), (0.01, 1, 0.2, 1), (0.01, 2, 0.2, 1)] if A else
           [(0, 1, 0.02, 0.5), (0, 1, 0.5, 0.5), (0, 1, 0.568, 0.5), (0.01, 2, 0.516, 0.5)])
    for ch, (lo, hi, d, sk), deg, nm in zip(chans, rng, (142, 120, 98, 76), 'ADSR'):
        x, y = polar(C, 120, deg)
        kc(ch, 'S', X(round(x)), round(y), lo, hi, d, sk, 0.001, nm, 'filter', 30)
    label('FILTER ENV' if A else 'AMP ENV', X(40), 262, 70, 9, INK2)
    # mixer / output: a curve sweeping toward the spine
    MIX = [('AmpSamp', 'SAMPLER', 0, 0.2, 0.005, 1), ('fVoice', 'KEYS', 0, 1, 0, 1), ('ampVCO', 'VCO', 0, 6, 2, 1),
           ('noise', 'NOISE', 0, 0.5, 0.341, 1), ('pLevel', 'POLYGON', 0, 1, 0.3, 1), ('oLevel', 'ODESSA', 0, 1, 0, 1)]
    OUTK = [('chorus', 'CHORUS', 0, 1, 0.25, 1), ('tone', 'TONE', 0.1, 6000, 800, 0.35), ('space', 'SPACE', 0, 1, 0.5, 1),
            ('reverb', 'REVERB', 0, 0.5, 0.126, 1), ('volume', 'OUTPUT', 0, 12, 3, 1), ('drive', 'DRIVE', 0, 1, 0.12, 1)]
    for (ch, nm, lo, hi, d, sk), (x, y) in zip(MIX if A else OUTK, [(270, 80), (302, 116), (322, 154), (330, 194), (314, 236), (300, 276)]):
        kc(ch, 'S', X(x), y, lo, hi, d, sk, 0.001, None, ('source' if A else (None if ch == 'volume' else 'fx')), 52)
        label(nm, X(x - 46), y - 5, 56, 10)
    label('MIXER' if A else 'OUTPUT', X(262), 50, 60, 10, INK2)
    # keys + swarm depth (lower wing)
    kc('bDepth' if A else 'lDepth', 'M', X(54), 314, 0, 1, 0.06, 1, 0.001, 'BOIDS' if A else 'LORENZ', None, 56)
    KL = [('fPitch', 'PITCH', -24, 24, 0, 1), ('fPos', 'POSITION', 0, 1, 0.3, 1), ('fSize', 'SIZE', 0.002, 1, 0.25, 0.4)]
    KR = [('fScatter', 'SCATTER', 0, 1, 0.1, 1), ('fSpeed', 'SPEED', 0.25, 2, 1, 0.6), ('glide', 'GLIDE', 0, 1, 0, 0.5)]
    for (ch, nm, lo, hi, d, sk), (x, y) in zip(KL if A else KR, [(122, 300), (174, 314), (226, 322)]):
        kc(ch, 'S', X(x), y, lo, hi, d, sk, 0.001, nm, 'motion' if ch == 'glide' else 'source', 52)
    toggle('fKey' if A else 'fRev', X(282), 316, 1 if A else 0, 'KEYTRACK' if A else 'REVERSE')
    label('KEYS', X(174), 274, 50, 10, INK2)
wings(wing)

# ---- tab selector: a shallow mirrored arc
TABS = [('tPoly', 'POLYGON'), ('tOde', 'ODESSA'), ('tLest', 'LESTER'), ('tMot', 'LFO'), ('tMat', 'MATRIX'), ('tSwarm', 'SWARM')]
if SONIC:
    TABS.append(('tSpace', 'SPACE'))
TAB_START = len(MAIN)
for i, (ch, nm) in enumerate(TABS):
    dx = (i - (len(TABS) - 1) / 2) * (96 if len(TABS) == 6 else 80)
    y = round(364 - 10 * (dx / 240) ** 2)
    ledbtn(ch, AX + dx, y, 1 if i == 0 else 0, '200', None, 12)
    label(nm, AX + dx, y + 13, 70, 9)
TAB_LINES = MAIN[TAB_START:]                               # drawn last so they sit above the matrix board
del MAIN[TAB_START:]
for ch, _ in TABS:
    P.pop(ch, None)



def page(name):
    global cur_page
    cur_page = name

# ---------------------------------------------------------------- polygon
page('polypanel')
c = PW / 2
screen(c - 100, 14, 200, 150)
put(f'signaldisplay bounds({round(c - 96)}, 18, 192, 142), colour(150, 255, 175, 255), backgroundColour(0, 0, 0, 0), '
    'displayType("lissajous"), signalVariable("adispX", "adispY"), zoom(-1)', 'disp', round(c - 96), 18, 192, 142)
COLS = [('pTune', 'TUNE', -24, 24, 0, 1, 1, 0), ('pOrder', 'ORDER', 2.1, 16, 4, 0.5, 2, 0.25),
        ('pTeeth', 'TEETH', 0, 1, 0, 1, 4, 0.35), ('pRoll', 'ROLL', 0, 1, 0, 1, 11, 0.3),
        ('pRatio', '1:N', 0.25, 16, 1, 0.4, 1, 0), ('pAmt', 'AMT', 0, 1, 0, 1, 6, 0.4)]
for i, (ch, nm, lo, hi, d, sk, js, ja) in enumerate(COLS):
    cx = [c - 216, c - 172, c - 128, c + 128, c + 172, c + 216][i]
    knob(f'j{i + 1}Att', 'S', cx, 6, -1, 1, ja, 1, 0.001, None, 'poly')
    vslider(ch, cx, 42, 90, lo, hi, d, sk, 'poly')
    label(nm, cx, 134, 44, 10)
    combo(f'j{i + 1}Src', cx, 148, 42, SRC, js, 14)
for (a, b), y in zip([(('pFM', 'FM IN', 0, 1, 0, 1), ('pWidth', 'WIDTH', 0, 1, 0.7, 1)),
                      (('pFold', 'FOLD', 0, 1, 0, 1), ('pPhase', 'SKEW', -1, 1, 0, 1)),
                      (('pSlew', 'SLEW', 0, 1, 0.02, 0.4), ('pSpin', 'SPIN', -10, 10, 0, 1))], (6, 66, 126)):
    knob(a[0], 'M', 80, y, a[2], a[3], a[4], a[5], 0.001, a[1], 'poly')
    knob(b[0], 'M', PW - 80, y, b[2], b[3], b[4], b[5], 0.001, b[1], 'poly')
for ch, dx, nm, d in [('pCycle', -60, 'CYCLE', 0), ('pRegular', 0, 'REGULAR', 0), ('pSnap', 60, 'OP RATIO', 1)]:
    ledbtn(ch, c + dx, 172, d, None, nm, 12, 60)

# ---------------------------------------------------------------- odessa
page('odepanel')
c = PW / 2
knob('oPart', 'L', c, 46, 1, 128, 32, 0.5, 1, 'PARTIALS', 'ode')
for i in range(12):
    a = math.radians(200 + i * (140 / 11))
    x = c + 64 * math.cos(a); y = 78 + 64 * math.sin(a)
    image(f'sp{i + 1}', 'led_on.png', round(x - 6), round(y - 6), 12, 12, ', alpha(0.06)', mirror=True)
for a, b, y in [(('oBank', 'BANK', -8, 8, 0, 1, 1), ('oFactor', 'FACTOR', -7, 7, 0, 1, 1), 6),
                (('oTension', 'TENSION', -1, 1, 0, 1, 0.001), ('oTilt', 'TILT', 0, 1, 0.5, 1, 0.001), 70),
                (('oFund', 'FUNDAMENTAL', 0, 1, 0, 1, 0.001), ('oWidth', 'ODD / EVEN', 0, 1, 0.8, 1, 0.001), 134)]:
    knob(a[0], 'M', c - 140, y, a[2], a[3], a[4], a[5], a[6], a[1], None if a[0] == 'oBank' else 'ode', lw=80)
    knob(b[0], 'M', c + 140, y, b[2], b[3], b[4], b[5], b[6], b[1], None if b[0] == 'oFactor' else 'ode', lw=80)
combo('oChord', c, 126, 110, ['unison', 'octaves', 'fifths', 'sus', 'major', 'minor', 'maj7', 'min7', 'add9',
                              'quartal', 'cluster', 'whole tone'], 1)
label('HEL CHORD', c, 143, 80, 9, INK2)
for i in range(8):
    ledbtn(f'oG{i + 1}', c + (i - 3.5) * 20, 160, 1, None, str(i + 1), 12, 18)
for (a, b), cx in zip([(('oTune', 'TUNE', -24, 24, 0, 1, 1), ('oDens', 'DENSITY', 0, 1, 0, 1, 0.001)),
                       (('oFine', 'FINE', -100, 100, 0, 1, 0.1), ('oWarp', 'WARP', 0, 1, 0, 1, 0.001)),
                       (('oSpread', 'SPREAD', 0, 1, 0.2, 1, 0.001), ('oPeak', 'PEAKING', 0, 1, 0.5, 1, 0.001))],
                      (50, 100, 150)):
    knob(a[0], 'S', cx, 6, a[2], a[3], a[4], a[5], a[6], a[1], 'ode', lw=50)
    knob(b[0], 'S', PW - cx, 6, b[2], b[3], b[4], b[5], b[6], b[1], 'ode', lw=50)
combo('oVoices', 100, 56, 96, ['1 voice', '3 voices', '5 voices'], 1)
combo('oFundWave', PW - 100, 56, 96, ['sine fundamental', 'square fundamental'], 1)
for (a, b), cx in zip([(('oExp', 'EXP FM'), ('oDen', 'DENSITY')), (('oLin', 'LIN FM'), ('oWarp', 'WARP'))], (70, 130)):
    for (ch, nm), x in ((a, cx), (b, PW - cx)):
        vslider(ch + 'Att', x, 82, 80, -1, 1, 0)
        label(nm + ' CV', x, 164, 54, 9)
        combo(ch + 'Src', x, 176, 52, SRC, 1, 14)

# ---------------------------------------------------------------- lester
page('lestpanel')
c = PW / 2
screen(c - 90, 8, 180, 58)
put(f'label bounds({round(c - 84)}, 16, 168, 12), text("A"), channel("lesA"), align("left"), fontColour(150, 255, 175, 255)',
    'disp', round(c - 84), 16, 168, 12, False)
put(f'label bounds({round(c - 84)}, 42, 168, 12), text("B"), channel("lesB"), align("left"), fontColour(150, 255, 175, 255)',
    'disp', round(c - 84), 42, 168, 12, False)
combo('link', c, 76, 110, ['link off', 'A ctl', 'series', '4pole', 'stereo'], 4, 16)
knob('lMix', 'M', c, 100, 0, 1, 1, 1, 0.001, 'A    MIX    B', 'filter', lw=90)
ledbtn('lRnd', c, 168, 0, None, 'RANDOMIZE', 12, 70)
P['lRnd'] = 0
DSTS = ['cutoff', 'resonance', 'mode', 'gain']
for X, sgn in (('a', -1), ('b', 1)):
    def xx(cx): return cx if sgn < 0 else PW - cx
    put(f'label bounds({round(xx(40) - 11)}, 10, 22, 18), text("{X.upper()}"), channel("les{X.upper()}n"), '
        'colour(0, 0, 0, 255), fontColour(220, 220, 220, 255)', 'badge', round(xx(40) - 11), 10, 22, 18)
    for k2, cx in zip(range(3), (110, 195, 280)):
        label(f'CV {k2 + 1}', xx(cx), 8, 50, 10)
        combo(f'{X}{k2 + 1}Src', xx(cx), 22, 76, SRC, 1, 15)
        if k2 == 0:
            label('> cutoff', xx(cx), 42, 76, 10, INK2)
        else:
            combo(f'{X}{k2 + 1}Dst', xx(cx), 40, 76, DSTS, [1, 3][k2 - 1], 15)
        knob(f'{X}{k2 + 1}Att', 'M', xx(cx), 64, -1, 1, 0, 1, 0.001, 'AMOUNT', None)
    label('LP > BP > HP > NOTCH > COMB', xx(195), 132, 200, 9, INK2)

# ---------------------------------------------------------------- motion
page('motpanel')
c = PW / 2
LX = [36, 86, 136, 186]
# header row: name + activity LED + switch, mirrored (left LFOs, right voice)
for (nm_l, led_l, sw_l, swlab_l), (nm_r, led_r, sw_r, swlab_r), cx in (
        (('LFO 1', 'l1Led', 'l1Sync', 'SYNC'), ('UNISON', 'vLed', 'uniLock', 'LOCK'), 61),
        (('LFO 2', 'l2Led', 'l2Sync', 'SYNC'), ('SUB', 'subLed', 'sub2', 'SUB-2'), 161)):
    label(nm_l, cx - 14, 2, 40, 10); label(nm_r, PW - cx + 14, 2, 40, 10)
    image(led_l, 'led_on.png', round(cx + 8), 2, 10, 10, ', alpha(0.15)'); image(led_r, 'led_on.png', round(PW - cx - 18), 2, 10, 10, ', alpha(0.15)')
    ledbtn(sw_l, cx + 36, 1, 0, None, None, 10); ledbtn(sw_r, PW - cx - 36, 1, 0, None, None, 10)
    label(swlab_l, cx + 36, 13, 24, 8, INK2); label(swlab_r, PW - cx - 36, 13, 24, 8, INK2)
image('fLed', 'led_on.png', 196, 76, 10, 10, ', alpha(0.1)'); image('oLed', 'led_on.png', PW - 206, 76, 10, 10, ', alpha(0.1)')
LEFT = [('l1Rate', 'RATE', 0.02, 20, 0.23, 0.35), ('l1Shape', 'SHAPE', 1, 6, 2, 1), ('l2Rate', 'RATE', 0.02, 20, 5.2, 0.35),
        ('l2Shape', 'SHAPE', 1, 6, 1, 1), ('meAtt', 'ATTACK', 0.001, 3, 0.005, 0.35), ('meDec', 'DECAY', 0.01, 4, 0.45, 0.35),
        ('fAtt', 'F.ATTACK', 0.001, 1, 0.01, 0.35), ('fRel', 'F.RELEASE', 0.005, 3, 0.25, 0.35), ('fGain', 'F.GAIN', 0, 4, 1, 0.5),
        ('dlyMix', 'DELAY', 0, 1, 0.14, 1), ('dlyTime', 'TIME', 1, 9, 6, 1), ('dlyFb', 'FEEDBACK', 0, 0.95, 0.35, 1)]
RIGHT = [('uni', 'UNISON', 1, 7, 3, 1), ('pEnv', 'P.ENV', -1, 1, 0, 1), ('sub', 'SUB', 0, 1, 0, 1),
         ('drift', 'DRIFT', 0, 1, 0.3, 1), ('spread', 'SPREAD', 0, 1, 0.6, 1), ('fm', 'FM', 0, 1, 0, 1),
         ('fmRatio', 'RATIO', 0.5, 8, 2, 1), ('fold', 'FOLD', 0, 1, 0, 1), ('vStereo', 'STEREO', 0, 1, 0.3, 1),
         ('resonate', 'RESONATE', 0, 1, 0, 1), ('velAmt', 'VELOCITY', 0, 1, 0.5, 1), ('bendRange', 'BEND', 0, 24, 2, 1)]
DISCRETE = {'l1Shape', 'l2Shape', 'dlyTime', 'uni', 'fmRatio', 'bendRange'}
for i in range(12):
    r, col = divmod(i, 4)
    y = 22 + r * 64
    a, b = LEFT[i], RIGHT[i]
    inc_a = 1 if a[0] in DISCRETE else 0.001
    inc_b = 1 if b[0] in ('uni', 'bendRange') else (0.5 if b[0] == 'fmRatio' else 0.001)
    knob(a[0], 'S', LX[col], y, a[2], a[3], a[4], a[5], inc_a, a[1], None if a[0] in DISCRETE else 'motion', lw=50)
    knob(b[0], 'S', PW - LX[col], y, b[2], b[3], b[4], b[5], inc_b, b[1], None if b[0] in DISCRETE else 'motion', lw=50)
label('ENV  /  FOLLOW', 111, 75, 120, 9, INK2); label('CHARACTER', PW - 111, 75, 120, 9, INK2)
label('FOLLOW  /  DELAY', 111, 139, 120, 9, INK2); label('MOTION', PW - 111, 139, 120, 9, INK2)
screen(c - 196, 22, 176, 150); screen(c + 20, 22, 176, 150)
put(f'signaldisplay bounds({round(c - 192)}, 26, 168, 142), colour(150, 255, 175, 255), backgroundColour(0, 0, 0, 0), '
    'displayType("waveform"), signalVariable("alfo1"), zoom(-1)', 'disp', round(c - 192), 26, 168, 142, False)
put(f'signaldisplay bounds({round(c + 24)}, 26, 168, 142), colour(150, 255, 175, 255), backgroundColour(0, 0, 0, 0), '
    'displayType("waveform"), signalVariable("alfo2"), zoom(-1)', 'disp', round(c + 24), 26, 168, 142, False)
label('LFO 1  SCOPE', c - 108, 176, 100, 10); label('LFO 2  SCOPE', c + 108, 176, 100, 10)

# ---------------------------------------------------------------- MATRIX: EMS-Synthi-style pin board
page('matpanel')
c = MW / 2
SRCS = SRC[1:]                     # 18 sources (rows)
DSTS_ = DST[1:]                    # 36 destinations (columns): 18 left | spine | 18 right
ABBR = {'Pitch': 'PCH', 'Cutoff': 'CUT', 'Resonance': 'RES', 'Pulse Width': 'PW', 'Fold': 'FLD', 'FM': 'FM', 'Sub': 'SUB',
        'Noise': 'NOI', 'Resonate': 'RSN', 'Detune': 'DTN', 'Amp': 'AMP', 'Pan': 'PAN', 'LFO 1 Rate': 'L1R', 'LFO 2 Rate': 'L2R',
        'Delay': 'DLY', 'Reverb': 'REV', 'Poly Order': 'P.OR', 'Poly Teeth': 'P.TE', 'Poly Roll': 'P.RL', 'Poly OP Amt': 'P.OA',
        'Poly Level': 'P.LV', 'Poly Fold': 'P.FD', 'Ode Partials': 'O.PA', 'Ode Tilt': 'O.TL', 'Ode Tension': 'O.TN',
        'Ode Density': 'O.DN', 'Ode Warp': 'O.WP', 'Ode Peaking': 'O.PK', 'Ode Level': 'O.LV', 'Field Pos': 'F.PS',
        'Field Size': 'F.SZ', 'Field Level': 'F.LV', 'B Cutoff': 'B.CT', 'Lester Mode': 'L.MD', 'Lester Mix': 'L.MX', 'Lester Gain': 'L.GN'}
ABBR.update({'Space Dist': 'S.DS', 'Space Azim': 'S.AZ', 'Space Elev': 'S.EL', 'Space Spread': 'S.SP',
             'Space Dev': 'S.DV', 'Space Air': 'S.AR'})
NR, NC = len(SRCS), len(DSTS_)
HR, HC = (NR + 1) // 2, NC // 2    # rows split round the tab gutter; columns split round the spine
PITCH_X = 21 if HC <= 18 else 19
PITCH_Y, ROW0 = 21, 44
GAP = 79                           # gutter between the two halves of the rows, where the page tabs sit
def row_y(r):
    return ROW0 + r * PITCH_Y + (GAP if r >= HR else 0)
DEFAULT_PINS = {(2, 3): 0.18, (11, 13): 0.35, (6, 3): 0.25, (3, 5): 0.15, (10, 2): 0.006, (12, 3): 0.1, (15, 3): 0.2, (17, 12): 0.3}
if SONIC:
    DEFAULT_PINS.update({(15, 40): 0.25, (6, 38): 0.3})   # boid x spreads each note's source, velocity sends it round
SPINE = 112
def col_x(j):
    if j < HC:
        return c - SPINE / 2 - (HC - j) * PITCH_X + PITCH_X / 2
    return c + SPINE / 2 + (j - HC) * PITCH_X + PITCH_X / 2
for j, dn in enumerate(DSTS_):
    label(ABBR[dn], col_x(j), 10 + ((j if j < HC else NC - 1 - j) % 2) * 12, 26, 9)
label('SOURCE', c, 16, 90, 10)
PINS = []
for r_, sn in enumerate(SRCS):
    y = row_y(r_)
    if sn.startswith('CC '):
        k_ = ord(sn[-1]) - ord('A')
        P[f'ccn{k_ + 1}'] = CC_DEFAULT[k_]
        label(sn, c - 37, y + 3, 36, 10)
        label('', c + 37, y + 3, 36, 10)
        put(f'nslider bounds({round(c - 17)}, {y}, 34, 16), channel("ccn{k_ + 1}"), range(0, 127, {CC_DEFAULT[k_]}, 1, 1), '
            f'colour(255, 255, 255, 255), fontColour(0, 0, 0, 255), textColour(0, 0, 0, 255), outlineColour(0, 0, 0, 255)',
            'combo', round(c - 17), y, 34, 16)
    else:
        label(sn.upper(), c, y + 3, SPINE - 8, 10)
    for j, dn in enumerate(DSTS_):
        ch = f'p{r_ + 2}_{j + 2}'
        dv = DEFAULT_PINS.get((r_ + 2, j + 2), 0)
        P[ch] = dv
        PINS.append((ch, r_ + 2, j + 2))
        x = round(col_x(j) - 8)
        put(f'rslider bounds({x}, {y}, 16, 16), channel("{ch}"), range(-1, 1, {dv}, 1, 0.001), filmstrip("pin.png", 64), '
            f'popupText("{sn} > {dn}"), automatable(0)', 'pin', x, y, 16, 16)
label('drag a pin up (green) or down (red) to patch it   -   centre = no pin', c, row_y(NR - 1) + PITCH_Y - 4, 420, 9, INK2)

page('swarmpanel')
c = PW / 2
screen(c - 200, 10, 180, 150); screen(c + 20, 10, 180, 150)
for i in range(8):
    image(f'bd{i + 1}', 'boid_dot.png', round(c - 110 + (i - 3.5) * 14), 80, 8, 8, '', mirror=False)
# the attractor as a trail of 24 fading dots (Cabbage's lissajous display can't hold a slow 2 s trail)
_lz = Image.new('RGBA', (12, 12), (0, 0, 0, 0)); ImageDraw.Draw(_lz).ellipse((1, 1, 10, 10), fill=(150, 255, 175, 255)); _lz.save(ROOT + 'src/lz_dot.png')
LZ_C = (c + 110, 85)
for i in range(24):
    image(f'lz{i}', 'lz_dot.png', round(LZ_C[0] - 3), LZ_C[1] - 3, 6, 6, f', alpha({1 - i / 26:.2f})', mirror=False)
label('BOIDS  (8 AGENTS)', c - 110, 164, 140, 10); label('LORENZ  ATTRACTOR', c + 110, 164, 140, 10)
for (a, b), (cx, y) in zip([(('bSpeed', 'SPEED', 0, 1, 0.35), ('lRate', 'RATE', 0, 1, 0.3)),
                            (('bCoh', 'COHESION', 0, 1, 0.5), ('lSigma', 'SIGMA', 2, 20, 10)),
                            (('bSep', 'SEPARATION', 0, 1, 0.5), ('lRho', 'RHO', 10, 50, 28)),
                            (('bAli', 'ALIGNMENT', 0, 1, 0.5), ('lBeta', 'BETA', 0.5, 5, 2.667))],
                           [(60, 14), (130, 14), (60, 84), (130, 84)]):
    knob(a[0], 'M', cx, y, a[2], a[3], a[4], 1, 0.001, a[1], None, lw=70)
    knob(b[0], 'M', PW - cx, y, b[2], b[3], b[4], 1, 0.001, b[1], None, lw=70)
SC = [('scSource', 'SOURCE'), ('scPoly', 'POLYGON'), ('scOde', 'ODESSA'), ('scFilt', 'FILTER'), ('scFx', 'FX'),
      ('scMot', 'MOTION'), ('scBoidV', 'V.BOIDS')]
for i, (ch, nm) in enumerate(SC):
    ledbtn(ch, c + (i - 3) * 46, 180, 1, None, nm, 12, 42)

NPTS = 22
RCX, RCY, RR = PW / 2, 104, 92                             # the radar (top view, front up, left to the left)
if SONIC:
    page('spacepanel')
    c = PW / 2
    screen(round(c - 104), 6, 208, 196)
    image('radar', f'{PFX}radar.png', round(c - 100), 8, 200, 192)
    for i in range(NPTS):
        spr = 'spv.png' if i < 12 else ('spf.png' if i < 18 else 'spx.png')
        image(f'spd{i}', spr, round(RCX - 4), RCY - 4, 8, 8, '', mirror=False)
    put(f'label bounds({round(c - 104)}, 206, 208, 10), text("FLOCK + LORENZ"), channel("spModeTxt"), align("centre"), {INK}',
        'label', round(c - 104), 206, 208, 10)
    SPK = [(('spMode', 'MODE', 0, 2, 0.6), ('spSpread', 'SPREAD', 0, 1, 0.15)),
           (('spSpeed', 'SPEED', 0, 1, 0.3), ('spDopp', 'DOPPLER', 0, 1, 0.5)),
           (('spDist', 'DISTANCE', 1, 12, 3), ('spAir', 'AIR', 0, 1, 0.4)),
           (('spHeight', 'HEIGHT', 0, 1, 0.5), ('spGrav', 'GRAVITY', 0, 1, 0.5)),
           (('spDev', 'DEVIATION', 0, 1, 0.3), ('spCoh', 'COHESION', 0, 1, 0.5)),
           (('spRot', 'ROTATE', -1, 1, 0), ('spFSplay', 'FIELD SPLAY', 0, 1, 0.6))]
    for (a, b), (cx, y) in zip(SPK, [(70, 16), (170, 16), (270, 16), (70, 110), (170, 110), (270, 110)]):
        knob(a[0], 'M', cx, y, a[2], a[3], a[4], 1, 0.001, a[1], 'motion', lw=76)
        knob(b[0], 'M', PW - cx, y, b[2], b[3], b[4], 1, 0.001, b[1], 'motion', lw=76)
    label('FLOCK  -  LORENZ  -  GRAVITY', 120, 196, 180, 9, INK2); label('16 CH  -  ACN / SN3D  -  3RD ORDER', PW - 120, 196, 180, 9, INK2)
cur_page = None

# =========================================================================== SYMMETRY CHECK
def check():
    bad = []
    for e in EL:
        if not e['mirror']: continue
        mxg = W - e['x'] - e['w']
        if not any(o['kind'] == e['kind'] and abs(o['x'] - mxg) <= 1 and abs(o['y'] - e['y']) <= 1 and
                   o['w'] == e['w'] and o['h'] == e['h'] and o['page'] == e['page'] for o in EL):
            bad.append(e)
    return bad
bad = check()
for b in bad:
    print('ASYMMETRIC:', b)
assert not bad, f'{len(bad)} elements without a mirror partner'

def overlaps():
    boxes = [e for e in EL if e['kind'] not in ('screen', 'lcd', 'frame', 'disp', 'box', 'plate') and e['mirror']]
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a['page'] != b['page'] and a['page'] and b['page']: continue
            if a['page'] != b['page'] and (a['page'] is None) != (b['page'] is None): continue
            if a['x'] < b['x'] + b['w'] - 1 and b['x'] < a['x'] + a['w'] - 1 and a['y'] < b['y'] + b['h'] - 1 and b['y'] < a['y'] + a['h'] - 1:
                hits.append((a, b))
    return hits
ov = overlaps()
for a_, b_ in ov[:40]:
    print('OVERLAP', a_['kind'], a_['page'], (a_['x'], a_['y'], a_['w'], a_['h']), '<->', b_['kind'], (b_['x'], b_['y'], b_['w'], b_['h']))
print('overlaps:', len(ov))

# =========================================================================== PANEL ART (late-90s render, topographic layers, 1x pixels)
from scipy.ndimage import gaussian_filter, shift as ndshift, distance_transform_edt
GREEN = np.array([115, 174, 138], float)
rng_ = np.random.default_rng(11)
NFR = 6                                                   # morph frames each way
NIDLE = int(os.environ.get('NIDLE', 120))                                               # idle-drift loop frames per page (24 fps -> a 5 s loop)
IDLE_FPS = 10
RINGS = [(0, 1.00), (7, 0.80), (15, 0.66), (24, 0.55), (34, 0.46), (45, 0.38), (57, 0.31), (70, 0.25), (84, 0.20)]

def brushed(h, w, amt, seed=0):
    r = np.random.default_rng(seed)
    return gaussian_filter(r.normal(0, 1, (h, w)), (0.4, 18)) * amt

BRUSH = brushed(H, W, 7, 1)
BACK = None
def back_panel():
    y = np.linspace(0, 1, H)[:, None]
    g = 46 - 16 * y + brushed(H, W, 6, 2)
    return np.repeat(g[..., None], 3, -1) * np.array([0.97, 1.0, 0.98])

def field_of(elems):
    f = np.zeros((H, W))
    for e in elems:
        if e['kind'] in ('disp', 'emblem'):
            continue
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2 + (5 if e['kind'].startswith('knob') else 0)
        rr = max(e['w'], e['h']) / 2 + (3 if e['kind'] == 'label' else 8)
        x0, x1 = int(max(0, cx - rr * 2.6)), int(min(W, cx + rr * 2.6))
        y0, y1 = int(max(0, cy - rr * 2.6)), int(min(H, cy + rr * 2.6))
        if x1 <= x0 or y1 <= y0: continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        f[y0:y1, x0:x1] += np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (rr * 0.85) ** 2))
    return f

_r = np.random.default_rng(21)
N1 = gaussian_filter(_r.normal(0, 1, (H, W)), 38); N1 /= N1.std()
N2 = gaussian_filter(_r.normal(0, 1, (H, W)), 38); N2 /= N2.std()
W1 = gaussian_filter(_r.normal(0, 1, (H, W)), 9); W1 /= W1.std()
W2 = gaussian_filter(_r.normal(0, 1, (H, W)), 9); W2 /= W2.std()
def _sym(a):                                              # mirror-symmetric about the centre line
    a = a + a[:, ::-1]
    return a / a.std()
N1, N2, W1, W2 = _sym(N1), _sym(N2), _sym(W1), _sym(W2)
def drift(theta):
    return math.cos(theta) * N1 + math.sin(theta) * N2, math.cos(theta) * W1 + math.sin(theta) * W2

def render_topo(F, theta=0.0):
    """stacked contour plates: outermost (darkest) first, the main plate last"""
    nf, wf = drift(theta)
    F = F + 0.045 * nf * np.clip(1 - F, 0, 1)            # the terrain breathes; controls stay on solid ground
    arr = back_panel()
    y = np.linspace(0, 1, H)[:, None]
    sheen = (1.10 - 0.22 * y)[..., None]
    core = F > 0.5
    dist = distance_transform_edt(~core)                 # distance outward from the main shape
    # organic wobble so the rings read as terrain, not offsets
    dist = dist + (wf * 5 + nf * 7) * np.clip(dist / 30, 0, 1)
    for D, fac in reversed(RINGS):
        m = (dist <= D).astype(float) if D > 0 else core.astype(float)
        sh = gaussian_filter(ndshift(m, (4, 3), order=0), 1.8)
        arr *= (1 - 0.5 * sh)[..., None]
        surf = GREEN[None, None, :] * fac * sheen + (BRUSH * fac)[..., None]
        hgt = gaussian_filter(m, 1.8)
        gy, gx = np.gradient(hgt)
        light = -(gx * 0.7 + gy * 0.7) * 9
        rim = (hgt < 0.97).astype(float) * m
        surf += (np.clip(light, -1, 1) * 80 * fac * rim)[..., None]
        arr = np.where(m[..., None] > 0, surf, arr)
        edge = (m > 0) & ((np.roll(m, 1, 0) == 0) | (np.roll(m, 1, 1) == 0) | (np.roll(m, -1, 0) == 0) | (np.roll(m, -1, 1) == 0))
        arr[edge] = np.array([14, 26, 19]) * (0.6 + 0.4 * fac)
    return arr

def details(img, elems):
    d = ImageDraw.Draw(img)
    for e in elems:
        x, y, w, h = e['x'], e['y'], e['w'], e['h']
        k = e['kind']
        if k == 'screen':
            d.rectangle((x - 2, y - 2, x + w + 1, y + h + 1), fill=(40, 46, 42))
            d.line((x - 2, y - 2, x + w + 1, y - 2), fill=(20, 24, 22)); d.line((x - 2, y - 2, x - 2, y + h + 1), fill=(20, 24, 22))
            d.line((x - 2, y + h + 1, x + w + 1, y + h + 1), fill=(225, 240, 228)); d.line((x + w + 1, y - 2, x + w + 1, y + h + 1), fill=(225, 240, 228))
            d.rectangle((x, y, x + w - 1, y + h - 1), fill=(6, 16, 10))
            for gy in range(y + 2, y + h, 3):
                d.line((x, gy, x + w - 1, gy), fill=(10, 26, 16))
        elif k == 'vslider':
            cx = x + w // 2
            d.rectangle((cx - 3, y + 4, cx + 2, y + h - 5), fill=(10, 14, 12))
            d.line((cx - 3, y + 4, cx + 2, y + 4), fill=(0, 0, 0)); d.line((cx - 3, y + h - 5, cx + 2, y + h - 5), fill=(220, 236, 224))
            for t in range(9):
                ty = y + 6 + (h - 12) * t // 8
                d.line((x - 2, ty, x + 2, ty), fill=(20, 40, 28)); d.line((x + w - 3, ty, x + w + 1, ty), fill=(20, 40, 28))
        elif k == 'emblem':
            lg = Image.open(ROOT + ('src/oblq_logo_sonic.png' if SONIC else 'src/oblq_logo.png')).convert('RGBA')
            lg = lg.resize((w, round(lg.height * w / lg.width)), Image.NEAREST)
            al = (np.asarray(lg)[..., 3] > 110).astype(float)
            hh, ww = al.shape
            yy = np.linspace(-1, 1, hh)[:, None]
            chrome = np.interp(yy, [-1, -0.25, 0, 0.12, 0.6, 1], [252, 205, 60, 110, 215, 150]) * np.ones((1, ww))
            rgb = np.stack([chrome * 0.95, chrome, chrome * 0.97], -1)
            oy_ = y + (h - hh) // 2
            base_ = np.asarray(img).astype(float)
            shm = ndshift(al, (3, 3), order=0)
            region = base_[oy_:oy_ + hh, x:x + ww]
            region *= (1 - 0.6 * shm)[..., None]
            outl = gaussian_filter(al, 0.8) > 0.05
            region[outl] = [12, 20, 16]
            region[al > 0] = rgb[al > 0]
            base_[oy_:oy_ + hh, x:x + ww] = region
            img.paste(Image.fromarray(base_.clip(0, 255).astype(np.uint8), 'RGB'))

def frame_img(F, page_elems, theta=0.0):
    im = Image.fromarray(render_topo(F, theta).clip(0, 255).astype(np.uint8), 'RGB')
    details(im, [e for e in EL if e['page'] is None] + page_elems)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(8, 10, 9)); d.line((1, 1, W - 2, 1), fill=(120, 130, 124)); d.line((1, 1, 1, H - 2), fill=(120, 130, 124))
    return im

PAGE_ORDER = ['polypanel', 'odepanel', 'lestpanel', 'motpanel', 'matpanel', 'swarmpanel'] + (['spacepanel'] if SONIC else [])
F_main = field_of([e for e in EL if e['page'] is None])
F_pg = {p_: field_of([e for e in EL if e['page'] == p_]) if p_ != 'matpanel' else np.zeros((H, W)) for p_ in PAGE_ORDER}
F_base = F_main + sum(F_pg.values()) / len(F_pg)
BG_FILES = []
import hashlib
BG_VERSION = 'topo-v4-sym'                                    # bump when render_topo / frame_img change
CACHE_FN = ROOT + 'src/.bgcache.json'
bgcache = json.load(open(CACHE_FN)) if os.path.exists(CACHE_FN) else {}
n_rendered = 0
def save_frame(fn, F, elems, theta=0.0):
    global n_rendered
    h = hashlib.sha1(); h.update(F.astype(np.float32).tobytes()); h.update(repr((elems, theta, RINGS, BG_VERSION, W, H)).encode())
    key = h.hexdigest()
    if bgcache.get(fn) != key or not os.path.exists(ROOT + 'src/' + fn):
        im = frame_img(F, elems, theta)
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(ROOT + 'src/' + fn, optimize=True)
        bgcache[fn] = key; n_rendered += 1
    BG_FILES.append(fn)
def ctrl_mask(elems):
    """1 under (and just round) every control: the land never leaves them"""
    m = np.zeros((H, W))
    for e in elems:
        if e['kind'] == 'emblem': continue
        m[max(0, int(e['y']) - 10):min(H, int(e['y'] + e['h']) + 10), max(0, int(e['x']) - 10):min(W, int(e['x'] + e['w']) + 10)] = 1
    return np.clip(gaussian_filter(m, 9) * 2.2, 0, 1)      # soft: the protected land has rounded shores
_yy, _xx = np.mgrid[0:H, 0:W]
def idle_field(FA, mask, phi, seed):
    """the whole landscape breathes: mirrored pairs of bulges and lakes travel round closed paths,
    so frame N wraps to frame 0; P(0) = 0 so the loop starts from the page's resting shape"""
    rg = np.random.default_rng(seed)
    def P(ph):
        out = np.zeros((H, W))
        for j in range(7):
            x0, y0 = rg.uniform(40, W / 2 - 20), rg.uniform(30, H - 30)
            ax, ay = rg.uniform(30, 120), rg.uniform(30, 110)
            m_, n_, k_ = rg.integers(1, 3), rg.integers(1, 3), rg.integers(1, 3)
            p_, q_, s_ = rg.uniform(0, 6.283, 3)
            r0, A = rg.uniform(45, 110), rg.uniform(0.35, 0.75) * (1 if j % 2 else -1)
            x = x0 + ax * math.cos(m_ * ph + p_); y = y0 + ay * math.sin(n_ * ph + q_)
            r = r0 * (1 + 0.3 * math.sin(ph + s_)); a = A * math.sin(k_ * ph + s_)
            for xc in (x, W - 1 - x):
                out += a * np.exp(-((_xx - xc) ** 2 + (_yy - y) ** 2) / (2 * r * r))
        rg.bit_generator.state = np.random.default_rng(seed).bit_generator.state
        return out
    F = FA + P(phi) - P(0.0)
    return np.maximum(F, 0.62 * mask)
for i, p_ in enumerate(PAGE_ORDER, 1):
    FA = F_main + F_pg[p_]
    MASK = ctrl_mask([e for e in EL if e['page'] is None or e['page'] == p_])
    for st in range(NFR + 1):
        t = st / NFR
        t = t * t * (3 - 2 * t)                          # ease in/out
        F = (1 - t) * FA + t * F_base
        save_frame(f'{PFX}bg_{i}_{st}.png', F, [e for e in EL if e['page'] == p_ and p_ != 'matpanel'] if st == 0 else [])
    for k in range(1, NIDLE):                              # idle loop (frame 0 is bg_i_0)
        save_frame(f'{PFX}bg_{i}_i{k}.png', idle_field(FA, MASK, 2 * math.pi * k / NIDLE, 100 + i), [e for e in EL if e['page'] == p_ and p_ != 'matpanel'], 2 * math.pi * k / NIDLE)
json.dump(bgcache, open(CACHE_FN, 'w'))
print('topography frames:', len(BG_FILES), '(rendered', n_rendered, ')')
bimg = Image.new('RGB', (MW, MH), (30, 34, 32)); bd = ImageDraw.Draw(bimg)
yy = np.linspace(0, 1, MH)[:, None]
plate = (GREEN[None, None, :] * (1.08 - 0.2 * yy)[..., None] + brushed(MH, MW, 6, 9)[..., None]).clip(0, 255)
bimg = Image.fromarray(plate.astype(np.uint8), 'RGB'); bd = ImageDraw.Draw(bimg)
bd.rectangle((0, 0, MW - 1, MH - 1), outline=(14, 26, 19)); bd.line((1, 1, MW - 2, 1), fill=(225, 245, 230)); bd.line((1, 1, 1, MH - 2), fill=(225, 245, 230))
bd.line((1, MH - 2, MW - 2, MH - 2), fill=(40, 70, 52)); bd.line((MW - 2, 1, MW - 2, MH - 2), fill=(40, 70, 52))
x0l, x1l = round(col_x(0) - 12), round(col_x(HC - 1) + 12); x0r, x1r = round(col_x(HC) - 12), round(col_x(NC - 1) + 12)
for (a_, b_) in ((x0l, x1l), (x0r, x1r)):
    for r0, r1 in ((0, HR - 1), (HR, NR - 1)):
        t_, b2 = row_y(r0) - 6, row_y(r1) + PITCH_Y - 6
        bd.rectangle((a_, t_, b_, b2), fill=(18, 24, 20))
        bd.line((a_, t_, b_, t_), fill=(4, 6, 5)); bd.line((a_, t_, a_, b2), fill=(4, 6, 5))
        bd.line((a_, b2, b_, b2), fill=(200, 225, 208)); bd.line((b_, t_, b_, b2), fill=(200, 225, 208))
        for r_ in range(r0 + 1, r1 + 1):
            ly = row_y(r_) - 6
            bd.line((a_ + 1, ly, b_ - 1, ly), fill=(34, 46, 38))
        for j in (range(HC) if a_ == x0l else range(HC, NC)):
            lx = round(col_x(j))
            bd.line((lx, t_ + 1, lx, b2 - 1), fill=(28, 38, 31))
bimg.save(ROOT + f'src/{PFX}board.png')
SPACE_FILES = []
if SONIC:
    def sprite(fn, col):
        im_ = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im_)
        d_.ellipse((2, 2, 13, 13), fill=(0, 0, 0, 160)); d_.ellipse((3, 3, 12, 12), fill=col + (255,))
        d_.ellipse((5, 4, 8, 7), fill=(255, 255, 255, 200)); im_.save(ROOT + 'src/' + fn); SPACE_FILES.append(fn)
    sprite('spv.png', (170, 255, 190)); sprite('spf.png', (255, 80, 60)); sprite('spx.png', (255, 200, 90))
    rim = Image.new('RGBA', (400, 384), (0, 0, 0, 0)); rd = ImageDraw.Draw(rim)
    cx_, cy_, r_ = 200, 192, RR * 2
    for k_ in (1, 2, 3):
        rr_ = r_ * k_ / 3
        rd.ellipse((cx_ - rr_, cy_ - rr_, cx_ + rr_, cy_ + rr_), outline=(80, 150, 100, 150 if k_ == 3 else 90), width=2)
    rd.line((cx_ - r_, cy_, cx_ + r_, cy_), fill=(80, 150, 100, 70), width=2); rd.line((cx_, cy_ - r_, cx_, cy_ + r_), fill=(80, 150, 100, 70), width=2)
    rd.polygon([(cx_, cy_ - r_ - 6), (cx_ - 8, cy_ - r_ + 10), (cx_ + 8, cy_ - r_ + 10)], fill=(150, 255, 175, 200))
    rd.ellipse((cx_ - 7, cy_ - 7, cx_ + 7, cy_ + 7), outline=(150, 255, 175, 220), width=2)
    rim.save(ROOT + f'src/{PFX}radar.png'); SPACE_FILES.append(f'{PFX}radar.png')

# ---- Ge'ez (Ethiopic) numerals for the sampler squares and the LCD readout, drawn as 2x art
from PIL import ImageFont
ETH_FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/KefaIII.ttf', 24)
LAT_FONT = ImageFont.truetype(ROOT + 'src/Tahoma Bold.ttf', 20)
ETH_FILES = []
for k_ in range(1, len(names) + 1):
    t_ = ethiopic(k_)
    im_ = Image.new('RGBA', (64, 24), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im_)
    bb = d_.textbbox((0, 0), t_, font=ETH_FONT)
    d_.text(((64 - (bb[2] - bb[0])) / 2 - bb[0], (24 - (bb[3] - bb[1])) / 2 - bb[1]), t_, font=ETH_FONT, fill=(8, 22, 14, 255), stroke_width=1, stroke_fill=(8, 22, 14, 255))
    im_.save(ROOT + f'src/eth_{k_}.png'); ETH_FILES.append(f'eth_{k_}.png')
    lc = Image.new('RGBA', (384, 24), (0, 0, 0, 0)); d_ = ImageDraw.Draw(lc)
    a_ = f'{NAME.upper()}   :   '
    wa = d_.textlength(a_, font=LAT_FONT); be = d_.textbbox((0, 0), t_, font=ETH_FONT)
    x0_ = (384 - wa - (be[2] - be[0])) / 2
    ba = d_.textbbox((0, 0), a_, font=LAT_FONT)
    d_.text((x0_, (24 - (ba[3] - ba[1])) / 2 - ba[1]), a_, font=LAT_FONT, fill=(150, 255, 175, 255))
    d_.text((x0_ + wa - be[0], (24 - (be[3] - be[1])) / 2 - be[1]), t_, font=ETH_FONT, fill=(150, 255, 175, 255), stroke_width=1, stroke_fill=(150, 255, 175, 255))
    lc.save(ROOT + f'src/{PFX}lcd_{k_}.png'); ETH_FILES.append(f'{PFX}lcd_{k_}.png')

# =========================================================================== CABBAGE TEXT
lines = [f'image bounds(0, 0, {W}, {H}), file("{PFX}bg_1_0.png"), channel("image6")'] + MAIN
for i, (pg_name, pl) in enumerate(PAGES.items()):
    vis = '' if pg_name == 'polypanel' else ', visible(0)'
    if pg_name == 'matpanel':
        lines.append(f'image bounds({MOX}, {MOY}, {MW}, {MH}), file("{PFX}board.png"), channel("{pg_name}"){vis} {{')
    else:
        lines.append(f'image bounds({POX}, {POY}, {PW}, {PH}), colour(0, 0, 0, 0), channel("{pg_name}"){vis} {{')
    lines += pl
    lines.append('}')
lines += TAB_LINES

# ---------------- presets
snaps = json.load(open(SNAPS_ORIG))
XL_PRESETS = json.load(open(ROOT + 'xl_presets.json'))
DROP = {'xlShow', 'fSel', 'fBed', 'tField', 'oV1', 'oV3', 'oV5', 'oFundSq', 'oFundSin'}
def fix(q):
    if any(f'src{i}' in q for i in range(1, 9)):
        for k_ in [k_ for k_ in q if k_.startswith('p') and '_' in k_ and k_[1:].replace('_', '').isdigit()]:
            q[k_] = 0
        slots = [(int(q.get(f'src{i}', 1)), int(q.get(f'dst{i}', 1)), float(q.get(f'amt{i}', 0))) for i in range(1, 9)]
    elif not any(k_.startswith('p') and '_' in k_ and k_[1:].replace('_', '').isdigit() and q[k_] for k_ in q):
        slots = [(si, di, a) for (si, di), a in DEFAULT_PINS.items()]
    else:
        slots = []
    for si, di, a in slots:
        if si > 1 and di > 1 and abs(a) > 0:
            q[f'p{si}_{di}'] = max(-1, min(1, q.get(f'p{si}_{di}', 0) + a))
    for i in range(1, 9):
        for k_ in ('src', 'dst', 'amt'):
            q.pop(f'{k_}{i}', None)
    if any(k in q for k in ('oV3', 'oV5')):
        q['oVoices'] = 3 if q.get('oV5') else (2 if q.get('oV3') else 1)
    if 'oFundSq' in q:
        q['oFundWave'] = 2 if q.get('oFundSq') else 1
    return {k: v for k, v in q.items() if k not in DROP}
xl = {}
for name, p in snaps.items():
    q = dict(p)
    for k2, v in P.items():
        q.setdefault(k2, v)
    xl[name] = fix(q)
for name, over in XL_PRESETS.items():
    q = dict(xl['Default']); q.update(over)
    xl[name] = fix(q)
json.dump(xl, open(SNAPS_XL, 'w'), indent=4)
names_txt = ', '.join(f'"{n}"' for n in xl)
lines[lines.index('@PRESETS@')] = (f'combobox bounds(40, 15, 260, 18), populate("{SNAPS_XL}"), channelType("string") channel("combo84") '
                                   f'value("Default") {COMBO} automatable(0) text({names_txt})')

cab = (f'\n// {NAME} - mirror-symmetric panel\n'
       f'form caption("{NAME}"), size({W}, {H}), pluginId("{'Oblc' if SONIC else 'Oblq'}"), colour(60, 64, 62, 255), guiMode("queue"), typeface("Tahoma Bold.ttf")\n' + '\n'.join(lines) + '\n')

# =========================================================================== ORC
NS = 8 + len(FILES)
sread = ['  ksel = gkNatSel'] + [f'  kSq{i} chnget "S{i}"' for i in range(1, NS + 1)]
for i in range(1, NS + 1):
    sread.append(f'  {"if" if i == 1 else "elseif"} kSq{i} > 0.5 then\n    ksel = {i}')
sread.append('  endif\n  gkNatSel = ksel')
slab = [f'  kslc{i} = (gkNatSel == {i} ? 1 : 0.5)\n  cabbageSet ksc + kfirst, "sl{i}", "alpha", kslc{i}'
        for i in range(1, NS + 1)]
orc = open(ROOT + 'engine.orc').read()
RND = [c for c in ('LPFreq', 'Res', 'aMode', 'aGain', 'bCut', 'bRes', 'bMode', 'bGain', 'mod', 'FAtt', 'FDec', 'FSus', 'FRel',
                   'pw', 'Tune1', 'detune', 'noise', 'pLevel', 'oLevel', 'pOrder', 'pTeeth', 'pRoll', 'pRatio', 'pAmt',
                   'oPart', 'oTilt', 'oTension', 'oDens', 'oWarp', 'oPeak', 'chorus', 'space', 'reverb', 'drive', 'fPos', 'fSize')
       if c in RANGE]
rnd = []
for c in RND:
    lo, hi, sk, sec = RANGE[c]
    if c in ('noise', 'pLevel', 'oLevel', 'reverb', 'drive'):
        hi = lo + (hi - lo) * 0.6          # keep levels sensible
    rnd.append(f'    cabbageSetValue "{c}", random:k({lo}, {hi}), krnt')
rnd.append(f'    cabbageSetValue "waveform", int(random:k(1, 4.99)), krnt')
# pick a random field recording / nature square and make sure it can be heard
rnd.append(f'    krsel = int(random:k(1, {NS} + 0.999))')
rnd += [f'    cabbageSetValue "S{i}", (krsel == {i} ? 1 : 0), krnt' for i in range(1, NS + 1)]
rnd.append('    cabbageSetValue "AmpSamp", random:k(0.03, 0.12), krnt')
pinread_l = ['  kpcnt init 0', '  kpcnt += 1', '  if kpcnt % 6 == 1 then', '    kpn = 0']
for ch, si, di in PINS:
    pinread_l += [f'    kpv chnget "{ch}"', '    if abs(kpv) > 0.0005 && kpn < 128 then',
                  f'      gkPinS[kpn] = {si}', f'      gkPinD[kpn] = {di}', '      gkPinA[kpn] = kpv', '      kpn += 1', '    endif']
pinread_l += ['    gkPinN = kpn', '  endif']
pinread = '\n'.join(pinread_l)
vu = '\n'.join(f'    cabbageSet 1, "vu{s}{i + 1}", "alpha", (kvd{s.lower()} > {-54 + i * 4.5} ? 1 : 0.12)' for s in 'LR' for i in range(12))
snames = ', '.join(f'"{ethiopic(i + 1)}"' for i in range(len(NATURE) + len(FILES)))
# swarm modulation: every continuous parameter rides its own boid coordinate and lorenz axis
gkmap = dict((ch, gk) for gk, ch in re.findall(r'^\s*(gk\w+) chnget "(\w+)"', orc, re.M))
SECIDX = {'source': 0, 'poly': 1, 'ode': 2, 'filter': 3, 'fx': 4, 'motion': 5}
gm = ['  ; ---- swarm modulation (generated): boids + lorenz on every continuous parameter']
n = 0
# the swarm moves timbre. Pitch, tuning, playback speed, levels and the drone switch stay where you put them
NO_SWARM = {'VCAinit', 'AmpSamp', 'fVoice', 'drive', 'volume', 'ampVCO', 'noise', 'pLevel', 'oLevel', 'sub', 'dlyMix', 'reverb',
            'velAmt', 'fGain', 'VCO', 'Tune1', 'fPitch', 'fSpeed', 'pTune', 'oTune', 'oFine', 'pRatio', 'pEnv', 'glide', 'vib'}
for ch, (lo, hi, sk, sec) in RANGE.items():
    gk = gkmap.get(ch)
    if not gk or ch in NO_SWARM: continue
    b, ax, la = n % 8, 'X' if (n // 8) % 2 == 0 else 'Y', 'XYZ'[n % 3]
    sgn = '-' if n % 2 else ''
    m = f'(gkSwB[{SECIDX[sec]}] * gkBoid{ax}[{b}] + gkSwL[{SECIDX[sec]}] * {sgn}gkLor{la})'
    if sk < 0.9 and lo > 0:
        gm.append(f'  {gk} limit {gk} * 2 ^ ({m} * 3), {lo}, {hi}')
    else:
        gm.append(f'  {gk} limit {gk} + {m} * {(hi - lo) * 0.5:.6g}, {lo}, {hi}')
    n += 1
print('swarm-modulated parameters:', n)
lzd = ['  ; ---- Lorenz trail on the SWARM page (generated)', '  klzt metro 12', '  if klzt == 1 then',
       '    klzi = 23', '    while klzi > 0 do', '      gkLzX[klzi] = gkLzX[klzi - 1]', '      gkLzY[klzi] = gkLzY[klzi - 1]', '      klzi -= 1', '    od',
       '    gkLzX[0] = gkLorX', '    gkLzY[0] = -gkLorZ', '  endif', '  if kcur == 6 && klzt == 1 then']
for i in range(24):
    lzd.append(f'    cabbageSet 1, "lz{i}", "bounds", int({LZ_C[0]} - 3 + limit(gkLzX[{i}], -1, 1) * 80), int({LZ_C[1]} - 3 + limit(gkLzY[{i}], -1, 1) * 64), 6, 6')
lzd.append('  endif')
lzdots = '\n'.join(lzd)
# MIDI CC rows: any channel, the most recently moved one wins; the CC number is chosen in the matrix spine
ccr = ['  ; ---- the four MIDI CC rows of the matrix (generated); polled every 8th control cycle', '  kccdec init 0', '  kccdec = (kccdec + 1) % 4', '  if kccdec != 0 kgoto CC_SKIP']
for k_ in range(1, 5):
    ccr += [f'  kccn{k_} chnget "ccn{k_}"', f'  kccc{k_} changed kccn{k_}', f'  if kccc{k_} == 1 then', f'    reinit CCR{k_}', '  endif',
            f'CCR{k_}:', f'  icn{k_} limit i(kccn{k_}), 0, 127']
    ccr += [f'  kc{k_}_{ch} ctrl7 {ch}, icn{k_}, 0, 1' for ch in range(1, 17)]
    ccr += ['  rireturn', f'  kcv{k_} init 0']
    for ch in range(1, 17):
        ccr += [f'  kd{k_}_{ch} changed kc{k_}_{ch}', f'  if kd{k_}_{ch} == 1 then', f'    kcv{k_} = kc{k_}_{ch}', '  endif']
    ccr += [f'  gkCC[{k_ - 1}] portk kcv{k_}, 0.01']
ccr.append('CC_SKIP:')
ccread = '\n'.join(ccr)
spd = []
if SONIC:
    spd = ['  ; ---- SPACE page: the radar (generated)', '  kspdt metro 20', '  if kcur == 7 && kspdt == 1 then',
           '    kRm = gkSpDist * 1.2']
    for i in range(NPTS):
        spd += [f'    kqx = gkPX[{i}] / kRm', f'    kqy = gkPY[{i}] / kRm', '    kql = sqrt(kqx * kqx + kqy * kqy)',
                '    if kql > 1 then', '      kqx = kqx / kql', '      kqy = kqy / kql', '    endif',
                f'    ksz limit 7 + gkPZ[{i}] / kRm * 6, 4, 12',
                f'    cabbageSet 1, "spd{i}", "bounds", int({RCX} - kqy * {RR} - ksz / 2), int({RCY} - kqx * {RR} - ksz / 2), int(ksz), int(ksz)']
    spd += ['  endif', '  kmb = round(gkSpMode * 2)', '  kmbc changed kmb', '  if kmbc + kfirst > 0 then',
            '    if kmb == 0 then', '      Smt strcpyk "FLOCK"', '    elseif kmb == 1 then', '      Smt strcpyk "FLOCK  +  LORENZ"',
            '    elseif kmb == 2 then', '      Smt strcpyk "LORENZ"', '    elseif kmb == 3 then', '      Smt strcpyk "LORENZ  +  GRAVITY"',
            '    else', '      Smt strcpyk "GRAVITY"', '    endif', '    cabbageSet 1, "spModeTxt", "text", Smt', '  endif']
spdots = '\n'.join(spd)
if SONIC:
    orc = '#define SONIC ##\n' + orc.replace('"bg_', f'"{PFX}bg_').replace('"lcd_', f'"{PFX}lcd_')
    rnd += [f'    cabbageSetValue "{c_}", random:k({lo_}, {hi_}), krnt' for c_, lo_, hi_ in
            (('spMode', 0, 2), ('spSpeed', 0.05, 0.7), ('spDev', 0, 0.8), ('spGrav', 0.1, 0.9), ('spCoh', 0, 1),
             ('spFSplay', 0.2, 1), ('spHeight', 0.2, 1), ('spRot', -0.4, 0.4))]
# level-match the recordings: one gain per file so they all sit near the same loudness
import wave as _wave
def _rms(fn):
    w_ = _wave.open(fn); a_ = np.frombuffer(w_.readframes(w_.getnframes()), '<i2').astype(float) / 32768
    return float(np.sqrt((a_ ** 2).mean()))
fnorm = ', '.join(f'{min(3.0, max(0.5, 0.09 / max(_rms(ROOT + "samples/" + f + ".wav"), 1e-4))):.3f}' for f in FILES)
orc = orc.replace('@FNORM@', fnorm)
orc = (orc.replace('@NSRC@', str(len(SRC))).replace('@NDST@', str(len(DST)))
          .replace('@FILES@', ', '.join(f'"{f}"' for f in FILES))
          .replace('@NCHNLS@', '16' if SONIC else '2').replace('@CCREAD@', ccread).replace('@SPDOTS@', spdots).replace('@LZDOTS@', lzdots)
          .replace('@SREAD@', '\n'.join(sread)).replace('@SLAB@', '\n'.join(slab)).replace('@GMOD@', '\n'.join(gm)).replace('@RND@', '\n'.join(rnd)).replace('@SNAMES@', snames).replace('@VU@', vu).replace('@NFR@', str(NFR)).replace('@NIDLE@', str(NIDLE)).replace('@IDLEFPS@', str(IDLE_FPS)).replace('@PINREAD@', pinread))

csd = f'''<Cabbage>{cab}</Cabbage>

<CabbageIncludes>
{chr(10).join(BG_FILES)}
{chr(10).join(ETH_FILES)}
{chr(10).join(SPACE_FILES)}
{PFX}board.png
pin.png
knob_big.png
knob_med.png
knob_small.png
sw_on.png
sw_off.png
btn_on.png
btn_off.png
slider_cap.png
led_on.png
vu_seg.png
Tahoma Bold.ttf
wv_sine.png
wv_saw.png
wv_tri.png
wv_square.png
boid_dot.png
lz_dot.png
</CabbageIncludes>

<CsoundSynthesizer>
<CsOptions>
-n -d -+rtmidi=NULL -M0 -m0d --displays
</CsOptions>
<CsInstruments>
{orc}
</CsInstruments>
<CsScore>
f0 z
</CsScore>
</CsoundSynthesizer>
'''
open(OUT, 'w', encoding='utf-8').write(csd)
print('wrote', OUT, len(csd), 'bytes;', len(xl), 'presets; elements', len(EL))
