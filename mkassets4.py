#!/usr/bin/env python3
"""ObliqSound in a late-90s 'rendered' plugin style (STS / CamelPhat era), drawn at 1x
with hard edges - chrome dome knobs, Win2000 bevel buttons, chunky slider caps."""
import math, numpy as np
from PIL import Image, ImageDraw
OUT = 'src/'
FR = 64
GREEN = np.array([115, 174, 138])

def chrome_knob(S, v):
    """sphere-lit chrome dome on a dark knurled collar; 1x pixels, no smoothing"""
    y, x = np.mgrid[0:S, 0:S].astype(float)
    c = (S - 1) / 2
    dx, dy = (x - c) / (S / 2), (y - c) / (S / 2)
    r = np.hypot(dx, dy)
    img = np.zeros((S, S, 4))
    ang = math.radians(135 + 270 * v)
    # collar (dark ring with knurls that turn)
    collar = (r <= 0.98) & (r > 0.70)
    th = np.arctan2(dy, dx)
    knurl = (np.cos((th - ang) * 24) > 0.2).astype(float)
    shade = 0.55 + 0.45 * (-(dx + dy) / 1.414)
    col = (40 + 40 * knurl * 0.6) * (0.6 + 0.6 * shade)
    for k in range(3):
        img[..., k] = np.where(collar, col, img[..., k])
    img[..., 3] = np.where(collar, 255, 0)
    # outline
    edge = (r <= 1.0) & (r > 0.94)
    for k in range(3): img[..., k] = np.where(edge, 12, img[..., k])
    img[..., 3] = np.where(edge, 255, img[..., 3])
    # dome
    dome = r <= 0.70
    rr = np.clip(r / 0.70, 0, 1)
    nz = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
    nx, ny = dx / 0.70, dy / 0.70
    L = np.array([-0.55, -0.65, 0.52]); L /= np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    # chrome environment banding: bright sky top, dark horizon, warm floor bounce
    env = np.interp(ny, [-1, -0.35, -0.05, 0.15, 0.6, 1], [250, 215, 70, 95, 170, 120])
    hx, hy, hz = L[0], L[1], L[2] + 1; hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip((nx * hx + ny * hy + nz * hz) / hn, 0, 1) ** 40
    lum = np.clip(env * (0.55 + 0.45 * diff) + 255 * spec, 0, 255)
    for k, tint in enumerate((0.96, 1.0, 0.98)):
        img[..., k] = np.where(dome, lum * tint, img[..., k])
    img[..., 3] = np.where(dome, 255, img[..., 3])
    im = Image.fromarray(img.astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    R = S / 2
    p0 = (c + R * 0.18 * math.cos(ang), c + R * 0.18 * math.sin(ang))
    p1 = (c + R * 0.66 * math.cos(ang), c + R * 0.66 * math.sin(ang))
    d.line([p0, p1], fill=(10, 10, 10, 255), width=max(2, S // 14))
    p2 = (c + R * 0.86 * math.cos(ang), c + R * 0.86 * math.sin(ang))
    d.point([p2], fill=(170, 255, 190, 255))
    return im

def strip(name, S):
    st = Image.new('RGBA', (S, S * FR), (0, 0, 0, 0))
    for i in range(FR):
        st.paste(chrome_knob(S, i / (FR - 1)), (0, i * S))
    st.save(OUT + name)
strip('knob_big.png', 60); strip('knob_med.png', 42); strip('knob_small.png', 32)

def bevel_btn(w, h, on, led=True):
    """Windows-2000 style raised button with a square LED window"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    face = (196, 200, 196) if not on else (210, 214, 210)
    d.rectangle((0, 0, w - 1, h - 1), fill=face + (255,))
    d.line((0, 0, w - 1, 0), fill=(255, 255, 255, 255)); d.line((0, 0, 0, h - 1), fill=(255, 255, 255, 255))
    d.line((0, h - 1, w - 1, h - 1), fill=(0, 0, 0, 255)); d.line((w - 1, 0, w - 1, h - 1), fill=(0, 0, 0, 255))
    d.line((1, h - 2, w - 2, h - 2), fill=(128, 128, 128, 255)); d.line((w - 2, 1, w - 2, h - 2), fill=(128, 128, 128, 255))
    if led:
        lw, lh = max(4, w // 2), max(3, h // 2)
        x0, y0 = (w - lw) // 2, (h - lh) // 2
        d.rectangle((x0, y0, x0 + lw - 1, y0 + lh - 1), fill=(150, 255, 175, 255) if on else (40, 70, 50, 255), outline=(60, 60, 60, 255))
        if on:
            d.line((x0 + 1, y0 + 1, x0 + lw - 2, y0 + 1), fill=(235, 255, 240, 255))
    return im
bevel_btn(14, 14, True).save(OUT + 'btn_on.png'); bevel_btn(14, 14, False).save(OUT + 'btn_off.png')
bevel_btn(32, 18, True).save(OUT + 'sw_on.png'); bevel_btn(32, 18, False).save(OUT + 'sw_off.png')

# chunky metal slider cap (STS style)
cap = Image.new('RGBA', (20, 12), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
for yy in range(12):
    g = int(235 - yy * 12)
    d.line((0, yy, 19, yy), fill=(g, g, g, 255))
d.rectangle((0, 0, 19, 11), outline=(20, 20, 20, 255)); d.line((1, 5, 18, 5), fill=(30, 30, 30, 255)); d.line((1, 6, 18, 6), fill=(255, 255, 255, 255))
cap.save(OUT + 'slider_cap.png')

# square LED + boid dot (phosphor green)
led = Image.new('RGBA', (10, 10), (0, 0, 0, 0)); d = ImageDraw.Draw(led)
d.rectangle((1, 1, 8, 8), fill=(150, 255, 175, 255), outline=(30, 60, 40, 255)); d.point((3, 3), fill=(255, 255, 255, 255))
led.save(OUT + 'led_on.png')
dot = Image.new('RGBA', (8, 8), (0, 0, 0, 0)); ImageDraw.Draw(dot).rectangle((2, 2, 5, 5), fill=(150, 255, 175, 255))
dot.save(OUT + 'boid_dot.png')
vu = Image.new('RGBA', (18, 8), (150, 255, 175, 255)); vu.save(OUT + 'vu_seg.png')
print('ok')

# ---------------- EMS-Synthi style patch pin (16x16, 64 frames):
# centre frames = empty hole; up = pin with green collar, down = red collar, brightness = amount
def pin_frame(v):
    S = 16; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((2, 2, 13, 13), fill=(150, 160, 152, 255))          # metal ring
    d.ellipse((4, 4, 11, 11), fill=(8, 10, 9, 255))               # hole
    d.point((5, 5), fill=(60, 66, 62, 255))
    a = abs(v)
    if a > 0.03:
        col = (60 + int(160 * a), 255, 110) if v > 0 else (255, 70 + int(60 * (1 - a)), 60)
        k = 0.35 + 0.65 * a
        cc = tuple(int(c * k) for c in col)
        d.ellipse((1, 1, 14, 14), fill=cc + (255,), outline=(10, 10, 10, 255))   # coloured collar
        d.ellipse((4, 3, 11, 10), fill=(235, 238, 236, 255), outline=(90, 94, 92, 255))  # pin head
        d.point((6, 5), fill=(255, 255, 255, 255)); d.point((7, 5), fill=(255, 255, 255, 255))
    return im
pst = Image.new('RGBA', (16, 16 * 64), (0, 0, 0, 0))
for i in range(64):
    pst.paste(pin_frame(-1 + 2 * i / 63), (0, i * 16))
pst.save(OUT + 'pin.png')
print('pin ok')
