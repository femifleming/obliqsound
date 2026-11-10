# =========================================================================== HEADER (CamelPhat-style plates)
def box(x, y, w, h, title=None, kind='box'):
    EL.append(dict(kind=kind, x=x + (POX if cur_page else 0), y=y + (POY if cur_page else 0), w=w, h=h, page=cur_page, mirror=True, title=title))
    if title:
        label(title, x + w / 2, y + 4, min(w - 20, 160), 11, TITLE)

box(20, 10, 290, 48, None, 'plate'); box(W - 310, 10, 290, 48, None, 'plate')
lg = Image.open(ROOT + 'src/oblq_logo.png'); lh = 26; lw_ = round(lg.width * lh / lg.height)
MAIN.append(f'image bounds({round(165 - lw_ / 2)}, {34 - lh // 2}, {lw_}, {lh}), file("oblq_logo.png"), channel("logo")')
MAIN.append('@PRESETS@')
MAIN.append(f'filebutton bounds({W - 300}, 37, 52, 15), populate("{SNAPS_XL}", "test"), text("SAVE", "SAVE"), mode("named preset") '
            'channel("filebutton85") colour:1(0, 0, 0, 0) colour:0(0, 0, 0, 0) fontColour:0(170, 200, 255, 230)')
MAIN.append(f'filebutton bounds({W - 244}, 37, 64, 15), populate("{SNAPS_XL}", "test"), text("REMOVE", "REMOVE"), mode("remove preset") '
            'channel("filebutton86") colour:1(0, 0, 0, 0) colour:0(0, 0, 0, 0) fontColour:0(170, 200, 255, 230)')
MAIN.append(f'combobox bounds({W - 94}, 36, 64, 16), mode("resize"), value(3) channel("PluginResizerCombBox") {COMBO}')
box(round(AX - 100), 12, 200, 40, None, 'plate')
P['rndAll'] = 0
MAIN.append(f'button bounds({round(AX - 92)}, 18, 184, 28), channel("rndAll"), text("RANDOMIZE", "RANDOMIZE"), '
            'colour:0(28, 32, 40, 255), colour:1(28, 32, 40, 255), fontColour:0(235, 240, 245, 255), fontColour:1(150, 240, 175, 255), '
            'outlineColour(0, 0, 0, 255), automatable(0)')

# =========================================================================== MAIN BODY (mirrored boxes)
def kc(ch, size, cx, cy, lo, hi, d, skew=1, inc=0.001, lab=None, sec=None, lw=56):
    knob(ch, size, cx, round(cy - KS[size] / 2), lo, hi, d, skew, inc, lab, sec, lw)

for A in (True, False):
    X = (lambda cx: cx) if A else (lambda cx: W - cx)
    bx = 20 if A else W - 300
    box(bx, 66, 280, 170, 'FILTER  A' if A else 'FILTER  B')
    kc('LPFreq' if A else 'bCut', 'L', X(78), 126, 35 if A else 20, 18000, 6548 if A else 18000, 0.35 if A else 0.25, 1,
       'CUTOFF', 'filter', 60)
    kc('Res' if A else 'bRes', 'M', X(156), 108, 0, 0.99 if A else 1, 0.12, 1, 0.001, 'RES', 'filter', 48)
    kc('aMode' if A else 'bMode', 'M', X(208), 108, 0, 4, 0, 1, 0.001, 'MODE', 'filter', 48)
    kc('aGain' if A else 'bGain', 'S', X(258), 110, 0, 1, 0.5, 1, 0.001, 'DRIVE', 'filter', 44)
    kc('mod' if A else 'VCAinit', 'S', X(78), 204, 0, 1, 1 if A else 0, 1, 0.001, 'ENV AMT' if A else 'VCA INIT', 'filter', 56)
    label('FILTER ENV' if A else 'AMP ENV', X(200), 158, 90, 9, INK2)
    chans = ['FAtt', 'FDec', 'FSus', 'FRel'] if A else ['AAtt', 'ADec', 'ASus', 'ARel']
    rng = ([(0.01, 1, 0.11, 1), (0, 1, 0.34, 1), (0.01, 1, 0.2, 1), (0.01, 2, 0.2, 1)] if A else
           [(0, 1, 0.02, 0.5), (0, 1, 0.5, 0.5), (0, 1, 0.568, 0.5), (0.01, 2, 0.516, 0.5)])
    for ch, (lo, hi, d, sk), x, nm in zip(chans, rng, (140, 180, 220, 260), 'ADSR'):
        kc(ch, 'S', X(x), 190, lo, hi, d, sk, 0.001, nm, 'filter', 34)

    box(bx, 244, 280, 112, 'MIXER' if A else 'OUTPUT')
    MIX = [('AmpSamp', 'SAMPLER', 0, 0.2, 0.005, 0.5), ('fVoice', 'KEYS', 0, 1, 0, 0.5), ('ampVCO', 'VCO', 0, 6, 2, 0.6),
           ('noise', 'NOISE', 0, 0.5, 0.341, 0.6), ('pLevel', 'POLYGON', 0, 1, 0.3, 0.6), ('oLevel', 'ODESSA', 0, 1, 0, 0.6)]
    OUTK = [('chorus', 'CHORUS', 0, 1, 0.25, 1), ('tone', 'TONE', 0.1, 6000, 800, 0.35), ('space', 'SPACE', 0, 1, 0.5, 1),
            ('reverb', 'REVERB', 0, 0.5, 0.126, 1), ('drive', 'DRIVE', 0, 1, 0.12, 1), ('volume', 'OUTPUT', 0, 12, 3, 0.6)]
    for (ch, nm, lo, hi, d, sk), x in zip(MIX if A else OUTK[::-1], (46, 88, 130, 172, 214, 256)):
        kc(ch, 'S', X(x), 292, lo, hi, d, sk, 0.001, nm, ('source' if A else (None if ch == 'volume' else 'fx')), 42)

    box(bx, 364, 280, 106, 'KEYS  ·  BOIDS' if A else 'KEYS  ·  LORENZ')
    kc('bDepth' if A else 'lDepth', 'M', X(62), 414, 0, 1, 0.06, 1, 0.001, 'SWARM', None, 50)
    KL = [('fPitch', 'PITCH', -24, 24, 0, 1), ('fPos', 'POSITION', 0, 1, 0.3, 1), ('fSize', 'SIZE', 0.002, 1, 0.25, 0.4)]
    KR = [('fScatter', 'SCATTER', 0, 1, 0.1, 1), ('fSpeed', 'SPEED', 0.25, 2, 1, 0.6), ('glide', 'GLIDE', 0, 1, 0, 0.5)]
    for (ch, nm, lo, hi, d, sk), x in zip(KL if A else KR, (124, 172, 220)):
        kc(ch, 'S', X(x), 412, lo, hi, d, sk, 0.001, nm, 'motion' if ch == 'glide' else 'source', 46)
    toggle('fKey' if A else 'fRev', X(268), 404, 1 if A else 0, 'KEYTRACK' if A else 'REVERSE')

# ---- centre: LCD (value readout + X/Y + VU), VCO, sampler
box(310, 66, 340, 234, None)
box(322, 76, 316, 216, None, 'screen')
put('label bounds(332, 82, 296, 15), text("OBLIQSOUND"), channel("lcdText"), align("centre"), fontColour(170, 205, 255, 255)',
    'disp', 332, 82, 296, 15, False)
label('VALUE  READOUT', AX, 99, 120, 8, LCD2)
label('X / Y   POLYGON', AX, 110, 120, 8, LCD2)
label('L', 341, 280, 18, 8, LCD2); label('R', W - 341, 280, 18, 8, LCD2)
for i in range(12):
    y = 268 - i * 13
    image(f'vuL{i + 1}', 'vu_seg.png', 332, y, 18, 8, ', alpha(0.12)')
    image(f'vuR{i + 1}', 'vu_seg.png', W - 350, y, 18, 8, ', alpha(0.12)')
put(f'signaldisplay bounds({round(AX - 112)}, 120, 224, 166), colour(170, 205, 255, 255), backgroundColour(0, 0, 0, 0), '
    'displayType("lissajous"), signalVariable("adispX", "adispY"), zoom(-1)', 'disp', round(AX - 112), 120, 224, 166)

box(310, 308, 340, 106, 'VCO')
kc('waveform', 'M', 356, 352, 1, 4, 3, 1, 1, 'WAVE', None, 40)
kc('Tune1', 'M', 418, 352, 1, 1.666, 1, 1, 0.01, 'FINE', 'source', 44)
kc('VCO', 'L', AX, 352, -15.674, 48, 0, 0.5, 0.1, 'PITCH', 'source', 50)
kc('pw', 'M', W - 418, 352, 0.01, 0.99, 0.5, 1, 0.01, 'P.WIDTH', 'source', 50)
kc('detune', 'M', W - 356, 352, 0, 1, 0.18, 1, 0.001, 'DETUNE', 'motion', 50)
for ch, fn, cx, y in [('Swave3', 'square.png', 324, 328), ('Swave2', 'saw2.png', 388, 328),
                      ('Swave4', 'saw.png', 324, 366), ('Swave1', 'sine.png', 388, 366)]:
    image(ch, fn, cx - 11, y, 22, 11, ', visible(0)' if ch != 'Swave2' else '', mirror=False)
for cx, y in ((W - 324, 328), (W - 388, 328), (W - 324, 366), (W - 388, 366)):
    pass
for ch, dx, d in [('OctDn', -24, 1), ('Oct0', 0, 0), ('OctUp', 24, 0)]:
    ledbtn(ch, AX + dx, 397, d, '104', None, 18)
label('-1 OCT', AX - 62, 398, 40, 9, INK2); label('+1 OCT', AX + 62, 398, 40, 9, INK2)

box(310, 420, 340, 50, 'SAMPLER')
names_full = [n.upper() for n in NATURE] + [SHORT.get(f, f) for f in FILES]
k = 0
for r in range(2):
    for j in range(13):
        k += 1
        cx = AX + (j - 6) * 24
        ledbtn(f'S{k}', cx, 434 + r * 17, 1 if k == 1 else 0, '100', None, 18)
        EL[-1]['popup'] = names_full[k - 1]

# ---- tabs box with selector pills in its header
box(20, 478, 920, 234, None)
TABS = [('tPoly', 'POLYGON'), ('tOde', 'ODESSA'), ('tLest', 'LESTER'), ('tMot', 'MOTION'), ('tSwarm', 'SWARM')]
for i, (ch, nm) in enumerate(TABS):
    cx = AX + (i - 2) * 100
    label(nm, cx, 482, 80, 10, TITLE)
    ledbtn(ch, cx, 494, 1 if i == 0 else 0, '200', None, 24)
for ch, _ in TABS:
    P.pop(ch, None)

