#!/usr/bin/env python3
"""Modern / organic controls (2x): matte knobs with a glowing value arc,
squircle 'pebble' buttons, pill switches, slider cap, LEDs."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = 'src/'
FR = 64
ACC = (255, 96, 74)

def radial(S, cx, cy, r, c0, c1, p=1.0):
    y, x = np.mgrid[0:S, 0:S]
    d = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1) ** p
    a = np.stack([c0[k] * (1 - d) + c1[k] * d for k in range(3)], -1)
    return Image.fromarray(a.astype(np.uint8), 'RGB')

def cmask(S, r, c, blur=0.7):
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).ellipse((c - r, c - r, c + r, c + r), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))

def knob(S, v, big=False):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); c = S / 2
    ring_r = S * 0.45; rw = max(2, S * 0.045)
    a0, a1 = 135, 135 + 270 * v
    d = ImageDraw.Draw(im)
    box = (c - ring_r, c - ring_r, c + ring_r, c + ring_r)
    d.arc(box, 135, 405, fill=(52, 52, 56, 255), width=int(rw))
    if v > 0.004:
        glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(glow).arc(box, a0, a1, fill=ACC + (170,), width=int(rw * 2.6))
        im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(S * 0.03)))
        ImageDraw.Draw(im).arc(box, a0, a1, fill=ACC + (255,), width=int(rw))
    # soft shadow + matte body
    br = S * (0.33 if not big else 0.345)
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).ellipse((c - br, c - br + S * .03, c + br, c + br + S * .05), fill=170)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(S * 0.04)))
    body = radial(S, c - S * .1, c - S * .14, br * 1.5, (78, 78, 82), (20, 20, 22), 1.1)
    im.paste(body.convert('RGBA'), (0, 0), cmask(S, br, c))
    d = ImageDraw.Draw(im)
    d.arc((c - br, c - br, c + br, c + br), 200, 290, fill=(140, 140, 146, 120), width=max(1, int(S * .012)))
    # indicator dot
    a = math.radians(a1)
    rr = br * 0.68; dr = S * (0.045 if not big else 0.04)
    d.ellipse((c + rr * math.cos(a) - dr, c + rr * math.sin(a) - dr, c + rr * math.cos(a) + dr, c + rr * math.sin(a) + dr),
              fill=(236, 236, 236, 255))
    return im

def strip(name, S, big=False):
    st = Image.new('RGBA', (S, S * FR), (0, 0, 0, 0))
    for i in range(FR):
        st.paste(knob(S, i / (FR - 1), big), (0, i * S))
    st.save(OUT + name)
strip('knob_big.png', 128, True); strip('knob_med.png', 96); strip('knob_small.png', 72)

def pebble(on, S=32):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).rounded_rectangle((3, 5, S - 3, S - 1), S * .38, fill=170)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(2)))
    body = radial(S, S * .4, S * .3, S * .8, (74, 74, 78) if not on else (120, 52, 44), (26, 26, 28) if not on else (60, 22, 18))
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).rounded_rectangle((2, 2, S - 3, S - 3), S * .36, fill=255)
    im.paste(body.convert('RGBA'), (0, 0), m)
    if on:
        g = Image.new('L', (S, S), 0); ImageDraw.Draw(g).ellipse((S * .25, S * .25, S * .75, S * .75), fill=230)
        im = Image.alpha_composite(im, Image.merge('RGBA', (Image.new('L', (S, S), ACC[0]), Image.new('L', (S, S), ACC[1]),
                                                             Image.new('L', (S, S), ACC[2]), g.filter(ImageFilter.GaussianBlur(S * .12)))))
    return im
pebble(True).save(OUT + 'btn_on.png'); pebble(False).save(OUT + 'btn_off.png')

def pill(on):
    W, H = 64, 36
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 4, W - 3, H - 5), (H - 9) / 2, fill=(26, 26, 28, 255) if not on else (110, 46, 38, 255),
                        outline=(70, 70, 74, 255) if not on else ACC + (255,), width=2)
    kx = W - 20 if on else 20
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).ellipse((kx - 12, 7, kx + 12, 31), fill=150)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(2)))
    k = Image.new('RGBA', (W, H), (0, 0, 0, 0)); kd = ImageDraw.Draw(k)
    kd.ellipse((kx - 11, 7, kx + 11, 29), fill=(214, 214, 218, 255) if on else (120, 120, 126, 255))
    return Image.alpha_composite(im, k)
pill(True).save(OUT + 'sw_on.png'); pill(False).save(OUT + 'sw_off.png')

cap = Image.new('RGBA', (40, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
d.rounded_rectangle((2, 3, 37, 21), 9, fill=(48, 48, 52, 255), outline=(10, 10, 10, 255))
d.line((10, 12, 29, 12), fill=ACC + (255,), width=3)
cap.save(OUT + 'slider_cap.png')

def led(S=32):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); c = S / 2
    g = Image.new('L', (S, S), 0); ImageDraw.Draw(g).ellipse((c - S * .45, c - S * .45, c + S * .45, c + S * .45), fill=200)
    im = Image.merge('RGBA', (Image.new('L', (S, S), ACC[0]), Image.new('L', (S, S), ACC[1]), Image.new('L', (S, S), ACC[2]),
                              g.filter(ImageFilter.GaussianBlur(S * .14))))
    ImageDraw.Draw(im).ellipse((c - S * .18, c - S * .18, c + S * .18, c + S * .18), fill=(255, 200, 190, 255))
    return im
led().save(OUT + 'led_on.png')
dot = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((3, 3, 12, 12), fill=ACC + (255,))
dot.filter(ImageFilter.GaussianBlur(0.6)).save(OUT + 'boid_dot.png')
print('ok')
