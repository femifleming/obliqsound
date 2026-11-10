from PIL import Image, ImageDraw, ImageFilter
bg = Image.open('/Users/Shared/KIA/Resources/background12.png').convert('RGB')
s = 1080/945
# clean band of the top panel (no labels): y 100..250 in 945-space
band = bg.crop((0, int(100*s), bg.size[0], int(250*s))).resize((945, 300), Image.BICUBIC)
panel = band.copy()
W, H = 945, 300
# outer frame colour like the device edge, recessed inner panel like the keyboard bed
mask = Image.new('L', (W, H), 0)
ImageDraw.Draw(mask).rounded_rectangle((8, 4, W-9, H-6), radius=12, fill=255)
edge = Image.new('RGB', (W, H), (52, 52, 52))
out = Image.composite(panel, edge, mask)
d = ImageDraw.Draw(out)
d.rounded_rectangle((8, 4, W-9, H-6), radius=12, outline=(64, 64, 64), width=2)
d.rounded_rectangle((10, 6, W-11, H-8), radius=11, outline=(30, 30, 30), width=1)
# thin separators between sections
for x in (198, 552, 788):
    d.line((x, 22, x, H-26), fill=(58, 58, 58), width=1)
out.save('src/xl_panel.png')
# small LED dot for LFO activity
led = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
ImageDraw.Draw(led).ellipse((6, 6, 17, 17), fill=(219, 240, 248, 255))
led = led.filter(ImageFilter.GaussianBlur(1.2))
led.save('src/xl_led.png')
print('ok')

# ---------------- polygon panel (replaces the keyboard area) ----------------
import math
W2, H2 = 945, 304
band2 = bg.crop((0, int(100*s), bg.size[0], int(250*s))).resize((W2, H2), Image.BICUBIC)
m2 = Image.new('L', (W2, H2), 0)
ImageDraw.Draw(m2).rounded_rectangle((8, 4, W2-9, H2-6), radius=12, fill=255)
p2 = Image.composite(band2, Image.new('RGB', (W2, H2), (52, 52, 52)), m2)
d = ImageDraw.Draw(p2)
d.rounded_rectangle((8, 4, W2-9, H2-6), radius=12, outline=(64, 64, 64), width=2)
d.rounded_rectangle((10, 6, W2-11, H2-8), radius=11, outline=(30, 30, 30), width=1)
# XY screen
d.rounded_rectangle((388, 18, 652, 206), radius=8, fill=(6, 6, 6), outline=(70, 70, 70), width=2)
for x in (370, 668):
    d.line((x, 22, x, H2-26), fill=(58, 58, 58), width=1)
# patch "cables" (polygogo style, in grey): knob -> down beside the slider -> jack
CG = (84, 84, 84)
for i in range(6):
    cx = 52 + i * 52
    d.line((cx - 20, 84, cx - 20, 244), fill=CG, width=2)
    d.arc((cx - 20, 238, cx - 4, 254), 90, 180, fill=CG, width=2)
    d.line((cx - 12, 254, cx - 4, 254), fill=CG, width=2)
# column icons
IC = (205, 205, 205)
def icon(i, kind):
    cx, cy = 52 + i * 52, 24
    if kind == 'note':
        d.ellipse((cx-7, cy+2, cx+1, cy+9), fill=IC); d.line((cx+1, cy+6, cx+1, cy-9), fill=IC, width=2)
        d.line((cx+1, cy-9, cx+6, cy-6), fill=IC, width=2)
    elif kind == 'hex':
        pts = [(cx + 9*math.cos(math.pi/6 + k*math.pi/3), cy + 9*math.sin(math.pi/6 + k*math.pi/3)) for k in range(6)]
        d.polygon(pts, outline=IC); d.line(pts + [pts[0]], fill=IC, width=2)
    elif kind == 'star':
        for k in range(3):
            a = k * math.pi / 3 + math.pi / 2
            d.line((cx - 9*math.cos(a), cy - 9*math.sin(a), cx + 9*math.cos(a), cy + 9*math.sin(a)), fill=IC, width=2)
    elif kind == 'roll':
        d.arc((cx-8, cy-8, cx+8, cy+8), 200, 520 - 40, fill=IC, width=2)
        d.polygon([(cx+8, cy+1), (cx+3, cy+6), (cx+11, cy+7)], fill=IC)
for i, k in enumerate(['note', 'hex', 'star', 'roll']):
    icon(i, k)
p2.save('src/poly_panel.png')
print('poly ok')

# ---------------- odessa / field / lester panels ----------------
def panel(fname, screens=(), seps=(), extra=None):
    p3 = Image.composite(band2, Image.new('RGB', (W2, H2), (52, 52, 52)), m2)
    d3 = ImageDraw.Draw(p3)
    d3.rounded_rectangle((8, 4, W2-9, H2-6), radius=12, outline=(64, 64, 64), width=2)
    d3.rounded_rectangle((10, 6, W2-11, H2-8), radius=11, outline=(30, 30, 30), width=1)
    for (x0, y0, x1, y1) in screens:
        d3.rounded_rectangle((x0, y0, x1, y1), radius=7, fill=(6, 6, 6), outline=(70, 70, 70), width=2)
    for x in seps:
        d3.line((x, 26, x, H2-26), fill=(58, 58, 58), width=1)
    if extra: extra(d3)
    p3.save('src/' + fname)
def ode_extra(d3):
    # arc guide behind the 12 spectrum LEDs, like Odessa's power-density arc
    d3.arc((420-104, 132-104, 420+104, 132+104), 196, 344, fill=(70, 70, 70), width=2)
    for x in (52, 112, 824, 884):   # slider "cable" ticks
        d3.line((x, 128, x, 250), fill=(84, 84, 84), width=1)
panel('ode_panel.png', seps=(196, 600), extra=ode_extra)
panel('field_panel.png', screens=[(20, 54, 590, 192)], seps=(600,))
def lest_extra(d3):
    d3.line((20, 146, 700, 146), fill=(58, 58, 58), width=1)
panel('lest_panel.png', screens=[(716, 30, 928, 104)], seps=(710,), extra=lest_extra)
led2 = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
ImageDraw.Draw(led2).ellipse((3, 3, 12, 12), fill=(235, 235, 235, 255))
led2.filter(ImageFilter.GaussianBlur(0.8)).save('src/xl_dot.png')
print('panels ok')
