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
for ch, fn, dx, y in [('Swave3', 'square.png', -34, 145), ('Swave2', 'saw2.png', 34, 145),
                      ('Swave4', 'saw.png', -34, 170), ('Swave1', 'sine.png', 34, 170)]:
    image(ch, RES + fn, round(AX + dx - 11), y, 22, 11, ', visible(0)' if ch != 'Swave2' else '')
for ch, dx, t, d in [('OctDn', -24, '-1', 1), ('Oct0', 0, '0', 0), ('OctUp', 24, '+1', 0)]:
    ledbtn(ch, AX + dx, 198, d, '104', t, 12, 22)

# ---- spine: sampler fan (three arcs around the pitch knob)
names = NATURE + [SHORT.get(f, f[:6]) for f in FILES]
arcs = [(names[0:8], 150), (names[8:17], 184), (names[17:26], 218)]
k = 0
for row, r in arcs:
    n = len(row); step = math.degrees(32 / r)
    for j, nm in enumerate(row):
        k += 1
        a = 90 + (j - (n - 1) / 2) * step
        x, y = polar((AX, 92), r, a)
        ledbtn(f'S{k}', x, round(y - 7), 1 if k == 1 else 0, '100', None, 14)
        label(nm, x, round(y + 8), 32, 9, 'fontColour(255, 255, 255, 120)', ch=f'sl{k}')
label('SAMPLER', AX, 226, 70, 10, INK2)

# ---- wings
def wing(A, X):
    C = (130, 124)
    kc('LPFreq' if A else 'bCut', 'L', X(C[0]), C[1], 35 if A else 20, 18000, 6548 if A else 18000, 1 if A else 0.25, 1,
       'CUTOFF A' if A else 'CUTOFF B', 'filter', 64)
    for (ch, size, deg, lo, hi, d, lab) in [
            ('Res' if A else 'bRes', 'M', -60, 0, 0.99 if A else 1, 0.12, 'RES'),
            ('aMode' if A else 'bMode', 'M', 5, 0, 4, 0, 'MODE'),
            ('aGain' if A else 'bGain', 'S', 62, 0, 1, 0.5, 'DRIVE'),
            ('mod' if A else 'VCAinit', 'S', 105, 0, 1, 1 if A else 0, 'ENV AMT' if A else 'VCA INIT')]:
        x, y = polar(C, 68, deg)
        kc(ch, size, X(round(x)), round(y), lo, hi, d, 1, 0.001, lab, 'filter', 52)
    label('FILTER A' if A else 'FILTER B', X(52), 92, 70, 10, INK2)
    chans = ['FAtt', 'FDec', 'FSus', 'FRel'] if A else ['AAtt', 'ADec', 'ASus', 'ARel']
    rng = ([(0.01, 1, 0.11, 1), (0, 1, 0.34, 1), (0.01, 1, 0.2, 1), (0.01, 2, 0.2, 1)] if A else
           [(0, 1, 0.02, 0.5), (0, 1, 0.5, 0.5), (0, 1, 0.568, 0.5), (0.01, 2, 0.516, 0.5)])
    for ch, (lo, hi, d, sk), deg, nm in zip(chans, rng, (150, 127, 104, 81), 'ADSR'):
        x, y = polar(C, 120, deg)
        kc(ch, 'S', X(round(x)), round(y), lo, hi, d, sk, 0.001, nm, 'filter', 30)
    label('FILTER ENV' if A else 'AMP ENV', X(40), 248, 70, 9, INK2)
    # mixer / output: a curve sweeping toward the spine
    MIX = [('AmpSamp', 'SAMPLER', 0, 0.2, 0.005, 1), ('fVoice', 'KEYS', 0, 1, 0, 1), ('ampVCO', 'VCO', 0, 6, 2, 1),
           ('noise', 'NOISE', 0, 0.5, 0.341, 1), ('pLevel', 'POLYGON', 0, 1, 0.3, 1), ('oLevel', 'ODESSA', 0, 1, 0, 1)]
    OUTK = [('chorus', 'CHORUS', 0, 1, 0.25, 1), ('tone', 'TONE', 0.1, 6000, 800, 0.35), ('space', 'SPACE', 0, 1, 0.5, 1),
            ('reverb', 'REVERB', 0, 0.5, 0.126, 1), ('volume', 'OUTPUT', 0, 12, 3, 1), ('drive', 'DRIVE', 0, 1, 0.12, 1)]
    for (ch, nm, lo, hi, d, sk), (x, y) in zip(MIX if A else OUTK, [(246, 64), (290, 90), (322, 126), (342, 168), (346, 212), (334, 256)]):
        kc(ch, 'S', X(x), y, lo, hi, d, sk, 0.001, nm, ('source' if A else (None if ch == 'volume' else 'fx')), 52)
    label('MIXER' if A else 'OUTPUT', X(300), 44, 60, 10, INK2)
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
TABS = [('tPoly', 'POLYGON'), ('tOde', 'ODESSA'), ('tLest', 'LESTER'), ('tMot', 'MOTION'), ('tSwarm', 'SWARM')]
for i, (ch, nm) in enumerate(TABS):
    dx = (i - 2) * 96
    y = round(364 - 10 * (dx / 192) ** 2)
    ledbtn(ch, AX + dx, y, 1 if i == 0 else 0, '200', None, 12)
    label(nm, AX + dx, y + 13, 70, 9)
for ch, _ in TABS:
    P.pop(ch, None)

