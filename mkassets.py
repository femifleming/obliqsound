#!/usr/bin/env python3
"""Photo-style hardware assets (rendered at 2x): knob filmstrips, toggle switch,
LED square buttons, slider cap, LEDs, and dark versions of the Kia artwork."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

OUT = 'src/'
FRAMES = 64

def radial(size, cx, cy, r, c0, c1, power=1.0):
    y, x = np.mgrid[0:size, 0:size]
    d = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1) ** power
    a = np.empty((size, size, 3))
    for k in range(3):
        a[..., k] = c0[k] * (1 - d) + c1[k] * d
    return Image.fromarray(a.astype(np.uint8), 'RGB')

def circle_mask(size, x0, y0, x1, y1, blur=0.6):
    m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).ellipse((x0, y0, x1, y1), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))

def knob_frame(S, angle, style):
    """S = frame size. style: 'big' (black skirt + brushed aluminium cap), 'med' (davies-style), 'small'."""
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    c = S / 2
    # drop shadow
    sh = Image.new('L', (S, S), 0)
    r_out = S * (0.47 if style != 'small' else 0.44)
    ImageDraw.Draw(sh).ellipse((c - r_out + S * .02, c - r_out + S * .05, c + r_out + S * .02, c + r_out + S * .05), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.035))
    im.paste((0, 0, 0, 255), (0, 0), sh)
    # skirt / body with knurling that turns with the knob
    body = radial(S, c - S * .12, c - S * .16, S * .62, (78, 78, 80), (14, 14, 15), 0.9).convert('RGBA')
    d = ImageDraw.Draw(body)
    ridges = 36 if style != 'small' else 24
    r_in = r_out * (0.70 if style == 'big' else 0.80)
    for i in range(ridges):
        a = angle + 2 * math.pi * i / ridges
        light = 0.5 + 0.5 * math.cos(a - math.radians(-135))     # lit from top-left
        col = int(22 + 38 * light)
        for w, cc in ((S * 0.018, (col, col, col + 2, 255)), (S * 0.006, (col + 30, col + 30, col + 32, 255))):
            d.line((c + r_in * math.cos(a), c + r_in * math.sin(a), c + r_out * math.cos(a), c + r_out * math.sin(a)),
                   fill=cc, width=max(1, int(w)))
    im.paste(body, (0, 0), circle_mask(S, c - r_out, c - r_out, c + r_out, c + r_out))
    # top cap
    r_cap = r_in * (0.98 if style == 'big' else 0.96)
    if style == 'big':
        cap = radial(S, c - S * .1, c - S * .14, S * .5, (232, 233, 235), (150, 152, 156), 1.1)
        arr = np.asarray(cap).astype(float)
        y, x = np.mgrid[0:S, 0:S]
        rr = np.hypot(x - c, y - c)
        arr += (np.sin(rr * 2.3) * 4 + np.random.default_rng(1).normal(0, 2.2, rr.shape))[..., None]   # spun-metal rings
        cap = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
        ind = (25, 25, 25, 255)
    else:
        cap = radial(S, c - S * .14, c - S * .18, S * .55, (70, 70, 74), (10, 10, 11), 1.0)
        ind = (245, 245, 245, 255)
    im.paste(cap.convert('RGBA'), (0, 0), circle_mask(S, c - r_cap, c - r_cap, c + r_cap, c + r_cap))
    d = ImageDraw.Draw(im)
    d.ellipse((c - r_cap, c - r_cap, c + r_cap, c + r_cap), outline=(0, 0, 0, 90), width=max(1, int(S * 0.012)))
    # indicator line (turns)
    r0 = r_cap * (0.30 if style == 'big' else 0.22)
    r1 = r_cap * 0.92 if style != 'small' else r_out * 0.95
    d.line((c + r0 * math.cos(angle), c + r0 * math.sin(angle), c + r1 * math.cos(angle), c + r1 * math.sin(angle)),
           fill=ind, width=max(2, int(S * (0.05 if style == 'small' else 0.04))))
    # soft specular highlight (fixed light)
    hl = Image.new('L', (S, S), 0)
    ImageDraw.Draw(hl).ellipse((c - r_cap * .8, c - r_cap * .9, c + r_cap * .1, c - r_cap * .05), fill=55 if style != 'big' else 80)
    hl = hl.filter(ImageFilter.GaussianBlur(S * 0.05))
    im = Image.alpha_composite(im, Image.merge('RGBA', (Image.new('L', (S, S), 255),) * 3 + (ImageChops.multiply(hl, circle_mask(S, c - r_cap, c - r_cap, c + r_cap, c + r_cap)),)))
    return im

def strip(name, S, style):
    st = Image.new('RGBA', (S, S * FRAMES), (0, 0, 0, 0))
    for i in range(FRAMES):
        a = math.radians(-225 + 270 * i / (FRAMES - 1))     # 7 o'clock -> 5 o'clock
        st.paste(knob_frame(S, a, style), (0, i * S))
    st.save(OUT + name)

strip('knob_big.png', 128, 'big')
strip('knob_med.png', 96, 'med')
strip('knob_small.png', 72, 'small')

# ---------------- toggle switch (bat lever) on/off, 2x
def toggle(up):
    S = 64; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2
    # hex nut
    pts = [(c + 15 * math.cos(math.pi / 6 + k * math.pi / 3), c + 15 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).polygon([(x + 1, y + 3) for x, y in pts], fill=140)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(2)))
    d.polygon(pts, fill=(176, 178, 182, 255), outline=(90, 90, 94, 255))
    d.ellipse((c - 10, c - 10, c + 10, c + 10), fill=(120, 122, 126, 255), outline=(70, 70, 74, 255))
    d.ellipse((c - 6, c - 6, c + 6, c + 6), fill=(40, 40, 42, 255))
    # bat
    dy = -1 if up else 1
    tip = (c, c + dy * 24)
    bat = Image.new('RGBA', (S, S), (0, 0, 0, 0)); bd = ImageDraw.Draw(bat)
    for w, col in ((9, (60, 62, 66, 255)), (7, (200, 202, 206, 255)), (3, (245, 245, 247, 255))):
        bd.line((c, c, tip[0], tip[1]), fill=col, width=w)
    bd.ellipse((tip[0] - 6, tip[1] - 6, tip[0] + 6, tip[1] + 6), fill=(214, 216, 220, 255), outline=(80, 80, 84, 255))
    bd.ellipse((tip[0] - 3, tip[1] - 4, tip[0] + 1, tip[1]), fill=(255, 255, 255, 255))
    im = Image.alpha_composite(im, bat)
    return im
toggle(True).save(OUT + 'sw_on.png'); toggle(False).save(OUT + 'sw_off.png')

# ---------------- square LED button (sampler / tabs / small switches), 2x
def ledbtn(on, S=32):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).rounded_rectangle((3, 5, S - 3, S - 1), 4, fill=160)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(1.5)))
    d.rounded_rectangle((2, 2, S - 3, S - 3), 4, fill=(36, 36, 38, 255), outline=(10, 10, 10, 255))
    d.rounded_rectangle((4, 4, S - 5, S - 6), 3, fill=(56, 56, 60, 255))
    lc = (255, 40, 30) if on else (70, 18, 16)
    g = Image.new('RGBA', (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.rounded_rectangle((9, 9, S - 10, S - 11), 2, fill=lc + (255,))
    if on:
        glow = Image.new('L', (S, S), 0); ImageDraw.Draw(glow).rounded_rectangle((6, 6, S - 7, S - 8), 3, fill=200)
        im.paste((255, 70, 50, 255), (0, 0), glow.filter(ImageFilter.GaussianBlur(3)))
    im = Image.alpha_composite(im, g)
    d = ImageDraw.Draw(im); d.line((10, 10, S - 12, 10), fill=(255, 255, 255, 110 if on else 40), width=1)
    return im
ledbtn(True).save(OUT + 'btn_on.png'); ledbtn(False).save(OUT + 'btn_off.png')

# ---------------- slider cap
cap = Image.new('RGBA', (40, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
d.rounded_rectangle((1, 2, 38, 22), 3, fill=(26, 26, 28, 255), outline=(0, 0, 0, 255))
d.rounded_rectangle((3, 3, 36, 11), 2, fill=(60, 60, 64, 255))
d.line((4, 12, 35, 12), fill=(240, 240, 240, 255), width=2)
cap.save(OUT + 'slider_cap.png')

# ---------------- LEDs (red), boid dot
def led(S, on):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2
    d.ellipse((c - S * .3, c - S * .3, c + S * .3, c + S * .3), fill=(40, 40, 40, 255))
    d.ellipse((c - S * .22, c - S * .22, c + S * .22, c + S * .22), fill=(255, 50, 40, 255) if on else (80, 20, 18, 255))
    if on:
        gl = Image.new('L', (S, S), 0); ImageDraw.Draw(gl).ellipse((c - S * .45, c - S * .45, c + S * .45, c + S * .45), fill=170)
        im = Image.alpha_composite(Image.merge('RGBA', (Image.new('L', (S, S), 255), Image.new('L', (S, S), 60), Image.new('L', (S, S), 40), gl.filter(ImageFilter.GaussianBlur(S * .12)))), im)
    ImageDraw.Draw(im).ellipse((c - S * .12, c - S * .16, c - S * .02, c - S * .06), fill=(255, 255, 255, 140))
    return im
led(32, True).save(OUT + 'led_on.png')
dot = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((3, 3, 12, 12), fill=(255, 70, 50, 255))
dot.filter(ImageFilter.GaussianBlur(0.6)).save(OUT + 'boid_dot.png')
gdot = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); ImageDraw.Draw(gdot).ellipse((3, 3, 12, 12), fill=(255, 60, 40, 255))
gdot.filter(ImageFilter.GaussianBlur(0.8)).save(OUT + 'xl_dot.png')

# ---------------- dark silkscreen versions of the Kia artwork
RES = '/Users/Shared/KIA/Resources/'
def ink(src, dst, col=(24, 24, 24)):
    a = Image.open(RES + src).convert('RGBA')
    r, g, b, al = a.split()
    lum = ImageOps.grayscale(a)
    alpha = ImageChops.multiply(al, lum.point(lambda v: 255 if v > 40 else int(v * 6)))
    Image.merge('RGBA', (Image.new('L', a.size, col[0]), Image.new('L', a.size, col[1]), Image.new('L', a.size, col[2]), alpha)).save(OUT + dst)
ink('kia_logo.png', 'logo_ink.png')
for w in ('sine', 'saw', 'saw2', 'square'):
    ink(w + '.png', w + '_ink.png')
print('assets ok')
