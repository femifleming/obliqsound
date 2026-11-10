#!/usr/bin/env python3
"""Symmetric background (1080x800) and tab-panel art for Kia instrument XL,
in the original's palette: dark graphite, soft grey outlines, rounded panels."""
import math
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 800
OUT = 'src/'

def grad():
    """vertical gradient with a centred soft glow - symmetric about x = W/2"""
    im = Image.new('RGB', (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            dx = (x - W / 2) / (W / 2)
            dy = (y - H * 0.35) / H
            g = 30 - 7 * (y / H) + 9 * math.exp(-(dx * dx * 1.6 + dy * dy * 5))
            px[x, y] = (int(g),) * 3
    return im

bg = grad()
d = ImageDraw.Draw(bg)
# device body
d.rounded_rectangle((4, 4, W - 5, H - 5), radius=22, outline=(62, 62, 62), width=2)
d.rounded_rectangle((7, 7, W - 8, H - 8), radius=20, outline=(20, 20, 20), width=1)

PANELS = [(20, 70, 310, 450), (320, 70, 440, 450), (450, 70, 630, 450), (640, 70, 760, 450), (770, 70, 1060, 450),
          (20, 460, 1060, 780)]
for (x0, y0, x1, y1) in PANELS:
    d.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=None, outline=(50, 50, 50), width=1)
    d.rounded_rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), radius=11, outline=(17, 17, 17), width=1)
# header rule
d.line((40, 60, W - 40, 60), fill=(44, 44, 44), width=1)
# oscilloscope window in the VCO panel
d.rounded_rectangle((462, 362, 618, 440), radius=7, fill=(6, 6, 6), outline=(66, 66, 66), width=2)
# thin dividers inside sampler (nature / field / keys) and filter (rows)
for y in (186, 306):
    d.line((44, y, 286, y), fill=(42, 42, 42), width=1)
for y in (254, 328):
    d.line((794, y, 1036, y), fill=(42, 42, 42), width=1)
bg.save(OUT + 'bg_xl.png')

# ---------------- tab panels: cut from the background so they line up ----------------
PX, PY, PW, PH = 20, 460, 1040, 320
base = bg.crop((PX, PY, PX + PW, PY + PH))
CX = PW // 2
CG = (78, 78, 78)
IC = (205, 205, 205)

def panel(name, fn):
    im = base.copy()
    dd = ImageDraw.Draw(im)
    fn(dd)
    im.save(OUT + name)

def screen(dd, x0, y0, x1, y1):
    dd.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=(6, 6, 6), outline=(70, 70, 70), width=2)

def poly(dd):
    screen(dd, CX - 130, 34, CX + 130, 214)
    cols = [CX - 274, CX - 222, CX - 170, CX + 170, CX + 222, CX + 274]
    for i, cx in enumerate(cols):
        sx = cx - 20 if i < 3 else cx + 20          # cables run on the outer side of each slider
        dd.line((sx, 90, sx, 240), fill=CG, width=2)
    for x in (CX - 330, CX + 330):
        dd.line((x, 30, x, 290), fill=(44, 44, 44), width=1)
    def icon(cx, kind, cy=26):
        if kind == 'note':
            dd.ellipse((cx - 7, cy + 2, cx + 1, cy + 9), fill=IC); dd.line((cx + 1, cy + 6, cx + 1, cy - 9), fill=IC, width=2)
            dd.line((cx + 1, cy - 9, cx + 6, cy - 6), fill=IC, width=2)
        elif kind == 'hex':
            pts = [(cx + 9 * math.cos(math.pi / 6 + k * math.pi / 3), cy + 9 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
            dd.line(pts + [pts[0]], fill=IC, width=2)
        elif kind == 'star':
            for k in range(3):
                a = k * math.pi / 3 + math.pi / 2
                dd.line((cx - 9 * math.cos(a), cy - 9 * math.sin(a), cx + 9 * math.cos(a), cy + 9 * math.sin(a)), fill=IC, width=2)
        elif kind == 'roll':
            dd.arc((cx - 8, cy - 8, cx + 8, cy + 8), 200, 480, fill=IC, width=2)
            dd.polygon([(cx + 8, cy + 1), (cx + 3, cy + 6), (cx + 11, cy + 7)], fill=IC)
    for cx, k in zip(cols[:4], ['note', 'hex', 'star', 'roll']):
        icon(cx, k)
panel('tab_poly.png', poly)

def ode(dd):
    dd.arc((CX - 104, 150 - 104, CX + 104, 150 + 104), 196, 344, fill=(70, 70, 70), width=2)
    for x in (CX - 290, CX + 290):
        dd.line((x, 30, x, 300), fill=(44, 44, 44), width=1)
    for cx in (CX - 420, CX - 360, CX + 360, CX + 420):
        dd.line((cx, 150, cx, 262), fill=CG, width=1)
panel('tab_ode.png', ode)

def lest(dd):
    screen(dd, CX - 100, 30, CX + 100, 104)
    for x in (CX - 125, CX + 125):
        dd.line((x, 30, x, 300), fill=(44, 44, 44), width=1)
    for x0, x1 in ((30, CX - 140), (CX + 140, PW - 30)):
        dd.line((x0, 112, x1, 112), fill=(44, 44, 44), width=1)
panel('tab_lest.png', lest)

def mot(dd):
    for x in (CX - 200, CX + 200):
        dd.line((x, 30, x, 300), fill=(44, 44, 44), width=1)
panel('tab_mot.png', mot)

# LED dots
led = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
ImageDraw.Draw(led).ellipse((6, 6, 17, 17), fill=(219, 240, 248, 255))
led.filter(ImageFilter.GaussianBlur(1.2)).save(OUT + 'xl_led.png')
dot = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
ImageDraw.Draw(dot).ellipse((3, 3, 12, 12), fill=(235, 235, 235, 255))
dot.filter(ImageFilter.GaussianBlur(0.8)).save(OUT + 'xl_dot.png')
print('ok')
