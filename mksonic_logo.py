#!/usr/bin/env python3
"""OBLIQSONIC wordmark: the ObliqSound logo with 'OUND' redrawn as 'ONIC' (same font, tracking, baseline)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label
lg = Image.open('src/oblq_logo.png').convert('RGBA'); a = np.asarray(lg)[..., 3]
H, W = a.shape
cols = (a > 60).any(0)
# glyph runs left to right: O B L I Q S O U N D TM
runs = []; x = 0
while x < W:
    if cols[x]:
        s = x
        while x < W and cols[x]: x += 1
        runs.append((s, x))
    x += 1
o2 = runs[6][0]                                   # the O after the swoop S
rows = np.where((a[:, runs[6][0]:runs[6][1]] > 60).any(1))[0]
top, bot = rows[0], rows[-1]
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 44)
Fs = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 14)
out = Image.new('RGBA', (W + 40, H), (0, 0, 0, 0))
out.paste(lg.crop((0, 0, o2 - 1, H)), (0, 0))
d = ImageDraw.Draw(out)
ob = d.textbbox((0, 0), 'O', font=F)
y = top - ob[1]
x = o2
for ch in 'ONIC':
    d.text((x, y), ch, font=F, fill=(245, 248, 246, 255))
    x += d.textlength(ch, font=F) * 1.18
d.text((x + 2, y - 4), 'TM', font=Fs, fill=(245, 248, 246, 255))
out = out.crop(out.getbbox())
out.save('src/oblq_logo_sonic.png'); print(len(runs), 'runs; O at', o2, 'logo', out.size)
