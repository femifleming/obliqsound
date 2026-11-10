#!/usr/bin/env python3
"""ObliqSound controls in a CamelPhat-3 style, with sage green instead of gold/orange (2x)."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
OUT = 'src/'
FR = 64
GREEN = (115, 174, 138)
LIT = (150, 240, 175)
BLUE_ON = (70, 120, 235)

def radial(S, cx, cy, r, c0, c1, p=1.0):
    y, x = np.mgrid[0:S, 0:S]
    d = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1) ** p
    return Image.fromarray(np.stack([c0[k] * (1 - d) + c1[k] * d for k in range(3)], -1).astype(np.uint8), 'RGB')

def cmask(S, r, c, blur=0.7):
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).ellipse((c - r, c - r, c + r, c + r), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))

def knob(S, v, ndots):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); c = S / 2
    # ring of LED dots (lit up to the value), like CamelPhat's orange dots
    rd = S * 0.455; dr = S * 0.032
    lit_n = v * (ndots - 1)
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(im)
    for i in range(ndots):
        a = math.radians(135 + 270 * i / (ndots - 1))
        x, y = c + rd * math.cos(a), c + rd * math.sin(a)
        on = i <= lit_n + 1e-6
        col = LIT if on else (40, 64, 50)
        d.ellipse((x - dr, y - dr, x + dr, y + dr), fill=col + (255,), outline=(20, 30, 24, 255))
        if on:
            gd.ellipse((x - dr * 2.4, y - dr * 2.4, x + dr * 2.4, y + dr * 2.4), fill=LIT + (120,))
    im = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S * 0.02)), im)
    # gunmetal knob with knurled skirt
    br = S * 0.355
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).ellipse((c - br, c - br + S * .03, c + br, c + br + S * .05), fill=190)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(S * 0.035)))
    skirt = radial(S, c - S * .12, c - S * .15, br * 1.6, (110, 116, 128), (22, 24, 30), 0.9).convert('RGBA')
    sd = ImageDraw.Draw(skirt); ang = math.radians(135 + 270 * v)
    for i in range(30):
        a = ang + 2 * math.pi * i / 30
        l = 0.5 + 0.5 * math.cos(a + math.radians(135))
        cc = int(30 + 50 * l)
        sd.line((c + br * .78 * math.cos(a), c + br * .78 * math.sin(a), c + br * math.cos(a), c + br * math.sin(a)),
                fill=(cc, cc + 2, cc + 6, 255), width=max(1, int(S * .016)))
    im.paste(skirt, (0, 0), cmask(S, br, c))
    cap = radial(S, c - S * .1, c - S * .13, br * 1.2, (92, 98, 110), (34, 36, 44), 1.0)
    im.paste(cap.convert('RGBA'), (0, 0), cmask(S, br * .78, c))
    d = ImageDraw.Draw(im)
    d.ellipse((c - br * .78, c - br * .78, c + br * .78, c + br * .78), outline=(10, 10, 14, 160), width=max(1, int(S * .012)))
    d.line((c + br * .2 * math.cos(ang), c + br * .2 * math.sin(ang), c + br * .74 * math.cos(ang), c + br * .74 * math.sin(ang)),
           fill=(240, 240, 240, 255), width=max(2, int(S * .045)))
    return im

def strip(name, S, ndots):
    st = Image.new('RGBA', (S, S * FR), (0, 0, 0, 0))
    for i in range(FR):
        st.paste(knob(S, i / (FR - 1), ndots), (0, i * S))
    st.save(OUT + name)
strip('knob_big.png', 128, 17); strip('knob_med.png', 96, 15); strip('knob_small.png', 72, 11)

def pill(on, W=40, H=24, r=5):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 2, W - 2, H - 1), r, fill=(0, 0, 0, 160))
    top, bot = ((140, 180, 255), (50, 90, 210)) if on else ((62, 70, 92), (24, 28, 40))
    g = np.linspace(0, 1, H)[:, None]
    arr = np.zeros((H, W, 3))
    for k in range(3): arr[..., k] = top[k] * (1 - g) + bot[k] * g
    body = Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((1, 0, W - 2, H - 3), r, fill=255)
    im.paste(body, (0, 0), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 0, W - 2, H - 3), r, outline=(10, 14, 24, 255), width=1)
    d.line((r, 1, W - r, 1), fill=(255, 255, 255, 150 if on else 50), width=1)
    if on:
        gl = Image.new('L', (W, H), 0); ImageDraw.Draw(gl).rounded_rectangle((4, 3, W - 5, H - 6), r, fill=90)
        im = Image.alpha_composite(im, Image.merge('RGBA', (Image.new('L', (W, H), 180), Image.new('L', (W, H), 210),
                                                            Image.new('L', (W, H), 255), gl.filter(ImageFilter.GaussianBlur(3)))))
    return im
pill(True).save(OUT + 'btn_on.png'); pill(False).save(OUT + 'btn_off.png')
pill(True, 64, 36, 9).save(OUT + 'sw_on.png'); pill(False, 64, 36, 9).save(OUT + 'sw_off.png')

# slider cap: green metallic, like the gold CamelPhat caps
cap = Image.new('RGBA', (44, 28), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
d.rounded_rectangle((1, 3, 42, 26), 3, fill=(0, 0, 0, 150))
g = np.linspace(0, 1, 24)[:, None]
arr = np.stack([np.full((24, 40), c) * (1.25 - 0.55 * g) for c in GREEN], -1).clip(0, 255)
cap.paste(Image.fromarray(arr.astype(np.uint8), 'RGB'), (2, 1))
d = ImageDraw.Draw(cap); d.rectangle((2, 1, 41, 24), outline=(30, 50, 38, 255)); d.line((4, 12, 39, 12), fill=(20, 30, 24, 255), width=3)
d.line((4, 2, 39, 2), fill=(230, 255, 238, 255), width=1)
cap.save(OUT + 'slider_cap.png')

# LEDs / VU segment / boid dot (light blue like the CamelPhat LCD)
def led(S, col):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); c = S / 2
    g = Image.new('L', (S, S), 0); ImageDraw.Draw(g).ellipse((c - S * .45, c - S * .45, c + S * .45, c + S * .45), fill=200)
    im = Image.merge('RGBA', tuple(Image.new('L', (S, S), v) for v in col) + (g.filter(ImageFilter.GaussianBlur(S * .14)),))
    ImageDraw.Draw(im).ellipse((c - S * .18, c - S * .18, c + S * .18, c + S * .18), fill=(235, 255, 240, 255))
    return im
led(32, LIT).save(OUT + 'led_on.png')
vu = Image.new('RGBA', (28, 8), (0, 0, 0, 0)); ImageDraw.Draw(vu).rectangle((0, 0, 27, 7), fill=(150, 190, 255, 255))
vu.save(OUT + 'vu_seg.png')
dot = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((3, 3, 12, 12), fill=(160, 200, 255, 255))
dot.filter(ImageFilter.GaussianBlur(0.6)).save(OUT + 'boid_dot.png')

# ---------------- ObliqSound logo (recreated; replaced by brand/obliqsound_logo.png if present)
import os
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand/obliqsound_logo.png')
if os.path.exists(src):
    im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(float)
    bright = a.min(-1)                                # white letters on green -> alpha from brightness
    alpha = np.clip((bright - 175) * 4, 0, 255)
    out = np.dstack([np.full(bright.shape, 245), np.full(bright.shape, 248), np.full(bright.shape, 246), alpha]).astype(np.uint8)
    lg = Image.fromarray(out, 'RGBA'); lg = lg.crop(lg.getbbox())
else:
    S = 4
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 44 * S)
    Fs = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 14 * S)
    lg = Image.new('RGBA', (560 * S, 90 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(lg)
    x = 4 * S; y = 18 * S
    def word(t, x):
        for ch in t:
            d.text((x, y), ch, font=F, fill=(245, 248, 246, 255))
            x += d.textlength(ch, font=F) * 1.18          # wide tracking like the original
        return x
    x = word('OBLIQ', x)
    # the swooping S: two tapered bezier strokes
    sx, sy, h = x + 4 * S, 6 * S, 74 * S
    def bez(p0, p1, p2, p3, n=80):
        return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
                 (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]) for t in np.linspace(0, 1, n)]
    pts = bez((sx + 30 * S, sy), (sx - 6 * S, sy + 18 * S), (sx + 40 * S, sy + 40 * S), (sx + 8 * S, sy + h))
    for i, (px, py) in enumerate(pts):
        w = (2 + 9 * math.sin(math.pi * i / (len(pts) - 1))) * S
        d.ellipse((px - w, py - w, px + w, py + w), fill=(245, 248, 246, 255))
    x = word('OUND', sx + 34 * S)
    d.text((x + 2 * S, y - 4 * S), 'TM', font=Fs, fill=(245, 248, 246, 255))
    lg = lg.crop(lg.getbbox()).resize((lg.getbbox()[2] // S - lg.getbbox()[0] // S, lg.getbbox()[3] // S - lg.getbbox()[1] // S), Image.LANCZOS)
lg.save(OUT + 'oblq_logo.png')
print('assets ok', lg.size)
