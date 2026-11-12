#!/usr/bin/env python3
"""ObliqSound / ObliqSonic manual -> manual/ObliqSound_ObliqSonic_Manual.pdf"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
IMG = ROOT + 'manual/img/'
OUT = ROOT + 'manual/ObliqSound_ObliqSonic_Manual.pdf'

pdfmetrics.registerFont(TTFont('Tahoma-Bold', ROOT + 'src/Tahoma Bold.ttf'))
pdfmetrics.registerFont(TTFont('Kefa', '/System/Library/Fonts/Supplemental/KefaIII.ttf'))

SAGE = colors.HexColor('#73AE8A')
SAGE_L = colors.HexColor('#E3EFE7')
SAGE_D = colors.HexColor('#3E6B50')
INK = colors.HexColor('#08160E')
GREY = colors.HexColor('#5B6B61')

ss = {
    'title': ParagraphStyle('title', fontName='Tahoma-Bold', fontSize=26, leading=30, textColor=colors.white, alignment=TA_CENTER),
    'sub': ParagraphStyle('sub', fontName='Helvetica', fontSize=12, leading=16, textColor=colors.white, alignment=TA_CENTER),
    'h1': ParagraphStyle('h1', fontName='Tahoma-Bold', fontSize=18, leading=22, textColor=SAGE_D, spaceBefore=4, spaceAfter=8),
    'h2': ParagraphStyle('h2', fontName='Tahoma-Bold', fontSize=12.5, leading=16, textColor=INK, spaceBefore=10, spaceAfter=4),
    'h3': ParagraphStyle('h3', fontName='Tahoma-Bold', fontSize=10, leading=13, textColor=SAGE_D, spaceBefore=6, spaceAfter=2),
    'p': ParagraphStyle('p', fontName='Helvetica', fontSize=9.6, leading=13.4, textColor=INK, spaceAfter=5),
    'li': ParagraphStyle('li', fontName='Helvetica', fontSize=9.6, leading=13.2, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=2),
    'cap': ParagraphStyle('cap', fontName='Helvetica-Oblique', fontSize=8.2, leading=10, textColor=GREY, alignment=TA_CENTER, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName='Helvetica', fontSize=8.4, leading=10.6, textColor=INK),
    'cellb': ParagraphStyle('cellb', fontName='Tahoma-Bold', fontSize=8.0, leading=10.4, textColor=INK),
    'note': ParagraphStyle('note', fontName='Helvetica', fontSize=9, leading=12.5, textColor=INK, backColor=SAGE_L,
                           borderPadding=(6, 7, 6, 7), spaceBefore=4, spaceAfter=9, leftIndent=2, rightIndent=2),
    'toc1': ParagraphStyle('toc1', fontName='Tahoma-Bold', fontSize=10.5, leading=15, textColor=INK),
    'toc2': ParagraphStyle('toc2', fontName='Helvetica', fontSize=9.4, leading=12.5, leftIndent=14, textColor=GREY),
}

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

story = []
def H1(t):
    story.append(CondPageBreak(60 * mm))
    p = Paragraph(t, ss['h1']); p.toc = (0, t); story.append(p)
def H2(t, toc=True):
    story.append(CondPageBreak(30 * mm))
    p = Paragraph(t, ss['h2'])
    if toc: p.toc = (1, t)
    story.append(p)
def H3(t): story.append(Paragraph(t, ss['h3']))
def P(t): story.append(Paragraph(t, ss['p']))
def NOTE(t): story.append(Paragraph(t, ss['note']))
def UL(items):
    for it in items: story.append(Paragraph(it, ss['li'], bulletText='•'))
    story.append(Spacer(1, 3))
def SHOT(fn, cap, w=170 * mm):
    im = Image(IMG + fn); r = im.imageHeight / im.imageWidth
    im.drawWidth, im.drawHeight = w, w * r
    story.append(KeepTogether([im, Paragraph(cap, ss['cap'])]))
def TABLE(rows, widths, head=True):
    data = [[Paragraph(str(c), ss['cellb'] if (head and i == 0) or j == 0 else ss['cell']) for j, c in enumerate(r)] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#C9D9CF')),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3), ('LEFTPADDING', (0, 0), (-1, -1), 4)]
    if head: st += [('BACKGROUND', (0, 0), (-1, 0), SAGE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(st)); story.append(t); story.append(Spacer(1, 7))
def CTRL(rows):           # control / range / what it does
    TABLE([['Control', 'Range', 'What it does']] + rows, [32, 26, 112])

# ============================================================== page furniture
class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if hasattr(f, 'toc'):
            lvl, txt = f.toc
            key = 'h%d' % id(f)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, level=lvl, closed=lvl > 0)
            self.notify('TOCEntry', (lvl, txt, self.page, key))

def cover(c, d):
    W, H = A4
    c.setFillColor(SAGE); c.rect(0, 0, W, H, stroke=0, fill=1)
    # topographic rings
    c.setLineWidth(1.1)
    for k in range(14):
        c.setStrokeColor(colors.Color(0.03 * k, 0.12 + 0.01 * k, 0.07, alpha=0.18 + 0.02 * k))
        c.ellipse(W / 2 - 60 * mm - k * 9 * mm, H * 0.52 - 70 * mm - k * 8 * mm, W / 2 + 60 * mm + k * 9 * mm, H * 0.52 + 70 * mm + k * 8 * mm)
    c.drawImage(IMG + 'icon.png', W / 2 - 22 * mm, H - 92 * mm, 44 * mm, 44 * mm, mask='auto')
    for i, n in enumerate(('logo_sound.png', 'logo_sonic.png')):
        im = Image(IMG + n); r = im.imageHeight / im.imageWidth
        c.drawImage(IMG + n, W / 2 - 60 * mm, H - 130 * mm - i * 30 * mm, 120 * mm, 120 * mm * r)
    c.setFillColor(colors.white); c.setFont('Tahoma-Bold', 22)
    c.drawCentredString(W / 2, 92 * mm, 'OWNER\'S MANUAL')
    c.setFont('Helvetica', 11.5)
    c.drawCentredString(W / 2, 82 * mm, 'Polyphonic synthesizer  /  field-recording sampler  /  third-order Ambisonics encoder')
    c.drawCentredString(W / 2, 75 * mm, 'VST3  -  Audio Unit  -  desktop app  (macOS)')
    c.setFont('Helvetica', 9); c.setFillColor(colors.HexColor('#0B2416'))
    c.drawCentredString(W / 2, 20 * mm, 'Version 2.1  -  November 2026')

def page(c, d):
    W, H = A4
    c.setStrokeColor(SAGE); c.setLineWidth(2); c.line(18 * mm, H - 14 * mm, W - 18 * mm, H - 14 * mm)
    c.setFont('Tahoma-Bold', 7.5); c.setFillColor(SAGE_D)
    c.drawString(18 * mm, H - 12 * mm, 'OBLIQSOUND  /  OBLIQSONIC')
    c.drawRightString(W - 18 * mm, H - 12 * mm, 'OWNER\'S MANUAL')
    c.setFont('Helvetica', 8); c.setFillColor(GREY)
    c.drawCentredString(W / 2, 10 * mm, str(d.page))

doc = Doc(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=18 * mm,
          title='ObliqSound / ObliqSonic - Owner\'s Manual', author='ObliqSound')
fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='f')
doc.addPageTemplates([PageTemplate('cover', [fr], onPage=cover), PageTemplate('body', [fr], onPage=page)])
story += [NextPageTemplate('body'), PageBreak()]

# ============================================================== contents
story.append(Paragraph('Contents', ss['h1']))
toc = TableOfContents(); toc.levelStyles = [ss['toc1'], ss['toc2']]
story += [toc, PageBreak()]

# ============================================================== 1 intro
H1('1  Welcome')
P('<b>ObliqSound</b> is a polyphonic synthesizer and field-recording instrument: a virtual-analogue voice, a '
  'polygonal oscillator, an additive (Odessa-style) oscillator, a dual morphing filter (Bionic-Lester-style), '
  'a sampler of 8 synthesized nature scenes and 18 field recordings, two LFOs, envelopes, a huge pin matrix '
  'in the spirit of the EMS Synthi, and a "swarm" of boids and a Lorenz attractor that can move every parameter.')
P('<b>ObliqSonic</b> is the same instrument as a <b>spatial sound source</b>. It plays from MIDI exactly like '
  'ObliqSound, but instead of a stereo pair it sends <b>16 channels of third-order Ambisonics</b> (ACN channel order, '
  'SN3D normalisation, the format of the IEM Plug-in Suite and SPARTA). Every voice you play, six copies of the '
  'field recording, the effects returns and the nature bed are points that fly round the listener on a flock, '
  'deviated Lorenz attractors or gravity wells, with distance, Doppler and air absorption.')
P('Both share one panel: a mirror-symmetric, organic layout in sage green, drawn like a late-90s rendered plug-in. '
  'Behind the controls is a topographic landscape that slowly drifts all the time and flows into a new shape '
  'whenever you change page.')
H2('What is in the box')
TABLE([['Item', 'Where it is installed'],
       ['ObliqSound.vst3, ObliqSonic.vst3', '~/Library/Audio/Plug-Ins/VST3/'],
       ['ObliqSound.component, ObliqSonic.component (Audio Units)', '~/Library/Audio/Plug-Ins/Components/'],
       ['ObliqSound.app, ObliqSonic.app (desktop apps)', '/Applications/'],
       ['Factory presets', 'inside each plug-in'],
       ['Your presets', '~/Library/Application Support/ObliqSound/presets.json  (and .../ObliqSonic/presets.json)']],
      [70, 100])
P('Both are instruments, listed under the manufacturer <b>ObliqSound</b>. The sound engine is SuperCollider\'s synthesis server, '
  'embedded in the plug-in: nothing else needs to be installed. There is no VST2 version.')
H2('Requirements')
UL(['macOS 11 or later, Apple silicon or Intel.',
    'A host that loads VST3 or Audio Unit instruments (REAPER, Ableton Live, Logic, Bitwig ...), or the desktop apps.',
    'For ObliqSonic: a host that can run a 16-channel track and an Ambisonics decoder (REAPER with the IEM Plug-in Suite or SPARTA '
    'is the reference set-up; see chapter 10).',
    'CPU: light. Sixteen voices with every layer on use roughly an eighth of one core at 48 kHz.'])

# ============================================================== 2 quick start
H1('2  Quick start')
H2('In a DAW')
UL(['Put <b>ObliqSound</b> on an instrument track and play. The default sound is a sawtooth through filter A with a little noise and the wind scene.',
    'Click the square buttons in the middle (the <b>sampler</b>) to choose a nature scene or a field recording; turn <b>SAMPLER</b> up to hear the bed, <b>KEYS</b> to play the recording from the keyboard.',
    'Click the page buttons under the display (POLYGON, ODESSA, LESTER, LFO, MATRIX, SWARM, and SPACE on ObliqSonic) to open the lower panel.',
    'Choose presets from the white list at the top left (133 included); <b>Randomize</b> rolls a new sound.',
    'Press <b>Help</b> (beside the preset list) or <b>F1</b> for the built-in help.'])
H2('As a desktop app')
UL(['Open <b>ObliqSound</b> or <b>ObliqSonic</b> from /Applications. The <b>Options</b> button at the top left opens the audio and MIDI settings (all MIDI inputs are enabled automatically, including ones you plug in later).',
    'With no keyboard attached, play from the computer keyboard (chapter 13).',
    'The app remembers the sound and the devices.'])
H2('ObliqSonic in REAPER (spatial)')
UL(['Insert <b>ObliqSonic</b> on a track. Click the track\'s <b>Route</b> button and set <b>Track channels: 16</b>.',
    'After it insert a decoder at <b>order 3, SN3D</b>: <b>IEM BinauralDecoder</b> for headphones or <b>IEM AllRADecoder</b> / '
    '<b>SPARTA AmbiDEC</b> for loudspeakers. Optionally add <b>IEM EnergyVisualizer</b> to watch the sound move.',
    'Play. Open the <b>SPACE</b> page to set how the points move.'])

# ============================================================== 3 panel overview
H1('3  The panel')
SHOT('sound_tPoly.jpg', 'ObliqSound with the POLYGON page open. The upper panel is always visible; the lower panel changes with the page buttons.')
P('Everything is placed in mirror symmetry about the centre line. The upper part is the instrument (oscillator spine in the middle, '
  'filters and envelopes on the wings, mixer and output in the shoulders, the sampler fan, the keys layer and the swarm depth at the bottom corners). '
  'The lower part is the page area, chosen by the seven (six on ObliqSound) page buttons in the arc under the display.')
H2('Header')
CTRL([['Preset list', '133 + yours', 'Recalls a preset. Presets include every control, the pins of the matrix and the CC numbers.'],
      ['Save', '-', 'Saves the current sound under a name you type.'],
      ['Remove', '-', 'Deletes a saved preset.'],
      ['Randomize', '-', 'Rolls a new sound: both filters, envelopes, oscillator, polygon and Odessa settings, the effects, the field-recording '
       'window, the waveform, and picks a <b>random sampler square</b> with an audible SAMPLER level. On ObliqSonic it also rolls the motion (mode, '
       'speed, deviation, gravity, cohesion, field splay, height, rotation).'],
      ['Help', '-', 'Opens the built-in help window (chapter 12). F1 does the same.'],
      ['Size', '50-200 %', 'Scales the whole window. The art is drawn at pixel resolution, so 100 % or 200 % look the sharpest.']])
H2('The living background')
P('The green plate is a topographic map: rings of darker and darker green step away from the area where the controls sit. '
  'It is never still. Mirrored pairs of bulges and lakes travel across the whole landscape, so the land swells, opens lakes between the controls '
  'and pulls its coast in and out, always symmetrically and never from under a control. Each page has 120 rendered shapes, stepped through ten times a second; '
  'the panel wanders back and forth through them at random, so the motion never repeats. '
  'When you change page the land first settles back to its resting shape, then flows through a shared middle shape into the next page\'s shape; the old controls leave first '
  'and the new ones arrive when the land has settled. The field recordings\' loop points drift on the same clock as the land (chapter 5).')

# ============================================================== 4 sound sources
H1('4  Voice: oscillators, mixer, filters, envelopes')
H2('Oscillator spine (centre)')
CTRL([['PITCH', '-15.7 .. +48 st', 'Coarse pitch of the whole instrument, in semitones (the big knob at the top).'],
      ['FINE', '1 .. 1.666', 'Fine tuning as a frequency ratio (up to about +8.8 semitones).'],
      ['WAVE', '4 positions', 'Waveform of the VCO: triangle, square/pulse, saw, sine (the icon beside the knob shows it).'],
      ['-1  0  +1', 'buttons', 'Octave down / normal / up.'],
      ['P.WIDTH', '0.01 .. 0.99', 'Pulse width of the square wave (also shapes the other waves slightly).'],
      ['DETUNE', '0 .. 1', 'Detune of the unison stack (see UNISON on the LFO page).'],
      ['VIBRATO', '0 .. 1', 'Amount of LFO 2 on pitch.']])
H2('Mixer (left shoulder)')
CTRL([['SAMPLER', '0 .. 0.2', 'Level of the ambient bed: the nature scene or field recording chosen in the sampler. The curve is gentle at the bottom so small moves stay controllable.'],
      ['KEYS', '0 .. 1', 'Level of the field recording played from the keyboard (the keys layer, chapter 5).'],
      ['VCO', '0 .. 6', 'Level (and drive) of the virtual-analogue oscillator stack.'],
      ['NOISE', '0 .. 0.5', 'Noise level; its colour is set by TONE in the output section.'],
      ['POLYGON', '0 .. 1', 'Level of the polygonal oscillator (POLYGON page).'],
      ['ODESSA', '0 .. 1', 'Level of the additive oscillator (ODESSA page). At 0 it is not computed at all, which saves CPU.']])
H2('Filter A and Filter B (wings)')
P('Each voice runs through a dual <b>Bionic-Lester-style</b> filter: a gain/overdrive stage into a two-pole state-variable filter whose '
  '<b>MODE</b> morphs continuously LP > BP > HP > notch > comb (all-pass at zero resonance, positive comb towards noon, negative comb past noon). '
  'How A and B are connected, and their CV inputs, are set on the LESTER page.')
CTRL([['CUTOFF A / B', '35 Hz .. 18 kHz', 'Cutoff of each filter. A follows the filter envelope (ENV AMT).'],
      ['RES', '0 .. 0.99', 'Resonance.'],
      ['MODE', '0 .. 4', 'Morphing response: 0 LP, 1 BP, 2 HP, 3 notch, 4 comb.'],
      ['DRIVE', '0 .. 1', 'Input gain into the filter; past the middle it overdrives (the A / B letter on the LESTER page lights inverted when clipping).'],
      ['ENV AMT', '0 .. 1', 'How far the filter envelope sweeps cutoff A.'],
      ['VCA INIT', '0 .. 1', 'Drone: after you let go, the last chord keeps sounding at this level until you play a new chord (polyphonic).']])
H2('Envelopes')
CTRL([['FILTER ENV  A D S R', 'A 0.01-1, D 0-1, S, R 0.01-2', 'The filter envelope (left wing).'],
      ['AMP ENV  A D S R', 'A 0-1, D 0-1, S, R 0.01-2', 'The amplitude envelope (right wing).']])
P('A third envelope, the <b>mod envelope</b> (ATTACK / DECAY on the LFO page), is a free modulation source, and <b>P.ENV</b> sends it to pitch.')
H2('Output (right shoulder)')
CTRL([['CHORUS', '0 .. 1', 'Three-tap ensemble chorus.'],
      ['TONE', '0.1 .. 6000', 'Colour of the noise generator (dark to bright).'],
      ['SPACE', '0 .. 1', 'Size and brightness of the reverb.'],
      ['REVERB', '0 .. 0.5', 'Reverb amount.'],
      ['OUTPUT', '0 .. 12', 'Master level (3 is unity).'],
      ['DRIVE', '0 .. 1', 'Master saturation before the effects (on ObliqSonic it is applied per voice, so the spatial image stays clean).']])
P('The master chain is drive > chorus > tempo-synced ping-pong delay (with a slightly wobbly, filtered feedback) > reverb > level > soft clip and limiter. '
  'Delay amount, time and feedback live on the LFO page.')

# ============================================================== 5 sampler
H1('5  The sampler: nature scenes and field recordings')
P('The fan of 26 square buttons in the middle chooses what the sampler plays. The squares are numbered in '
  '<b>Ge\'ez (Ethiopic) numerals</b>; the display under the fan shows the current number. Squares 1-8 are synthesized '
  'nature scenes (generated live, never the same twice); squares 9-26 are field recordings: 8-second, 16-bit loops cut from the '
  'middle of longer recordings.')
num = ' ፩፪፫፬፭፮፯፰፱'
ten = ' ፲፳'
def eth(n): return (ten[n // 10] if n >= 10 else '') + (num[n % 10] if n % 10 else '')
NAT = ['wind', 'birds', 'beach', 'geyser', 'forest', 'water', 'thunder', 'night']
FILES = open(ROOT + 'samples/index.txt').read().split()
rows = [['', 'No.', 'Source']]
lst = [(i + 1, 'nature: ' + NAT[i]) for i in range(8)] + [(9 + i, 'recording: ' + f) for i, f in enumerate(FILES)]
half = (len(lst) + 1) // 2
data = [['Sq.', 'Numeral', 'Plays', 'Sq.', 'Numeral', 'Plays']]
for i in range(half):
    r = []
    for k in (i, i + half):
        if k < len(lst):
            n, s = lst[k]
            r += [Paragraph(str(n), ss['cellb']), Paragraph(f'<font name="Kefa" size="12">{eth(n)}</font>', ss['cell']), Paragraph(esc(s), ss['cell'])]
        else:
            r += ['', '', '']
    data.append(r)
data[0] = [Paragraph(c, ss['cellb']) for c in data[0]]
t = Table(data, colWidths=[10 * mm, 18 * mm, 57 * mm] * 2, repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), SAGE), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                       ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#C9D9CF')), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
story += [t, Spacer(1, 8)]
H2('The ambient bed')
P('<b>SAMPLER</b> (mixer) sets the level of the chosen square as a continuous bed. For field recordings the bed loops a window of the '
  'file whose <b>start and end points are always slowly sliding</b>: the start wanders over the first half of the file and the loop length '
  'over 30-80 % of it, at the same unhurried pace as the drifting background. So the bed never repeats exactly. <b>SPEED</b> sets its playback rate '
  'and <b>REVERSE</b> plays it backwards.')
H2('The keys layer')
P('<b>KEYS</b> (mixer) turns the recording into a playable instrument: every note micro-loops a piece of the recording.')
CTRL([['PITCH', '-24 .. +24 st', 'Transposition of the keys layer.'],
      ['POSITION', '0 .. 1', 'Where in the file the note\'s loop sits (also drifts slowly with the loop points).'],
      ['SIZE', '0.002 .. 1', 'Loop length, from a grain to the whole file (also breathes slowly).'],
      ['KEYTRACK', 'on / off', 'On: the keys play the recording chromatically. Off: every key plays it at its own pitch.'],
      ['SCATTER', '0 .. 1', 'Each note starts at a random offset around POSITION.'],
      ['SPEED', '0.25 .. 2', 'Playback rate of the bed.'],
      ['REVERSE', 'on / off', 'Plays the bed backwards.'],
      ['GLIDE', '0 .. 1', 'Portamento between notes (for all the voice\'s oscillators).']])
H2('Audio followers')
P('Two envelope followers turn audio into modulation: <b>Follower</b> listens to the sampler (bed + keys layer + nature), <b>Output</b> listens to the '
  'whole instrument. Their attack, release and gain are on the LFO page (F.ATTACK, F.RELEASE, F.GAIN). Use them in the matrix like any source.')
NOTE('<b>Nature resonator:</b> the RESONATE knob (LFO page) lets the selected nature scene ring through a waveguide tuned to each note, '
     'so wind or rain takes on the pitch of what you play.')

# ============================================================== 6 pages
H1('6  The pages')
H2('POLYGON - the polygonal oscillator')
P('Inspired by the E-RM Polygogo: a waveform made by tracing a polygon in X/Y. A continuous ORDER (number of sides, fractions allowed) and '
  'TEETH (star-shape) make the timbre; ROLL rotates it; a phase-modulation operator (1:N, AMT) adds sidebands. The screen draws the polygon live.')
CTRL([['TUNE (slider)', '-24 .. +24', 'Pitch of the polygon relative to the VCO.'],
      ['ORDER', '2.1 .. 16', 'Number of sides, continuous.'],
      ['TEETH', '0 .. 1', 'Star-ness: pulls alternate vertices inward.'],
      ['ROLL', '0 .. 1', 'Rotation of the shape (one turn).'],
      ['1:N', '0.25 .. 16', 'Ratio of the phase-modulation operator.'],
      ['AMT', '0 .. 1', 'Amount of the operator.'],
      ['Jacks (knob + list above/below each slider)', '-1 .. 1 / source', 'Each slider has a jack: choose a modulation source in the list and its amount with the small knob (attenuverter).'],
      ['FM IN', '0 .. 1', 'Audio-rate FM from the VCO.'],
      ['FOLD', '0 .. 1', 'Wavefolder on the polygon output.'],
      ['SLEW', '0 .. 1', 'Glide time for ORDER and TEETH changes, so the shape morphs instead of jumping.'],
      ['WIDTH', '0 .. 1', 'Stereo width: the X trace goes left and the Y trace right; at 0 both are mixed to the centre.'],
      ['SKEW', '-1 .. 1', 'Phase skew of the trace.'],
      ['SPIN', '-10 .. 10', 'Precession: the polygon rotates continuously at this rate.'],
      ['CYCLE', 'on / off', 'Precession: the polygon turns once every ORDER periods, so its corners walk round the cycle.'],
      ['REGULAR', 'on / off', 'Quantises ORDER to whole numbers.'],
      ['OP RATIO', 'on / off', 'Snaps 1:N to musical ratios.']])
SHOT('sound_tOde.jpg', 'The ODESSA page.')
H2('ODESSA - the additive oscillator')
P('After the XAOC Devices Odessa: up to 128 partials per voice with spectral tilt, tension (stretching), a comb-like density filter, '
  'warping and peaking, split into two banks, eight partial-group gates and a chord mode that stacks up to five voices.')
CTRL([['PARTIALS', '1 .. 128', 'Number of partials.'],
      ['TILT', '0 .. 1', 'Spectral slope: dark to bright.'],
      ['TENSION', '-1 .. 1', 'Stretches or squeezes the partial series (bell and string-like inharmonicity).'],
      ['DENSITY', '0 .. 1', 'A sweeping comb over the spectrum (the Odessa "density" filter).'],
      ['WARP', '0 .. 1', 'Warps the comb across the spectrum.'],
      ['PEAKING', '0 .. 1', 'Sharpness of the comb peaks.'],
      ['BANK', '-8 .. 8', 'Splits partials into two alternating banks (A left, B right) in groups of |BANK|; the sign picks which bank is retuned by FACTOR.'],
      ['FACTOR', '-7 .. 7', 'Frequency factor of the retuned bank (x2, x3 ... or /2, /3 ...).'],
      ['FUNDAMENTAL + list', '0 .. 1', 'Adds a sine or square fundamental under the stack.'],
      ['ODD / EVEN', '0 .. 1', 'Stereo width of the two banks (A left, B right); at 0 both banks sit in the middle.'],
      ['HEL CHORD + voices', '12 chords; 1/3/5', 'Stacks voices as unison, octaves, fifths, sus, major, minor, maj7, min7, add9, quartal, cluster or whole tone.'],
      ['Gates 1-8', 'on / off', 'Mute or pass the eight groups of partials.'],
      ['TUNE / FINE / SPREAD', '', 'Coarse and fine pitch, and detune spread of the chord voices.'],
      ['EXP FM, LIN FM, DENSITY, WARP CV', '-1 .. 1 / source', 'Four CV sliders, each with a source list (any matrix source).']])
P('The 12 LEDs above PARTIALS are a spectrum strip; in version 2 they are not animated.')
SHOT('sound_tLest.jpg', 'The LESTER page: CV inputs for A and B, the OLED read-out, the link mode and the A/B mix.')
H2('LESTER - the dual filter in depth')
CTRL([['Link mode', '5 modes', '<b>link off</b>: A on the left, B on the right, mixed by MIX. <b>A ctl</b>: B\'s cutoff follows A. <b>series</b>: A then B. '
       '<b>4pole</b>: B copies A and is in series (a steeper slope). <b>stereo</b>: A processes the left channel and B the right.'],
      ['A  MIX  B', '0 .. 1', 'Balance between the outputs of A and B.'],
      ['CV 1-3 (per filter)', 'source / dest / -1..1', 'Three CV inputs per filter: pick a source, a destination (cutoff, resonance, mode, gain) and an amount. CV 1 always goes to cutoff.'],
      ['RANDOMIZE', 'button', 'Rolls both filters (like the module\'s "randomize current").'],
      ['OLED', '-', 'Shows each filter\'s cutoff, resonance and mode.']])
SHOT('sound_tMot.jpg', 'The LFO page with its two scopes.')
H2('LFO - modulators, voice character, delay')
CTRL([['LFO 1 / 2  RATE', '0.02 .. 20 Hz', 'LFO speed. With SYNC on it snaps to musical divisions of the host tempo.'],
      ['SHAPE', '1 .. 6', 'Sine, triangle, saw, square, sample & hold, smooth random.'],
      ['ATTACK / DECAY', 'seconds', 'The mod envelope (a matrix source; P.ENV sends it to pitch).'],
      ['F.ATTACK / F.RELEASE / F.GAIN', '', 'Response and sensitivity of the audio followers.'],
      ['DELAY / TIME / FEEDBACK', '', 'Ping-pong delay: amount, time in note values (1/32 .. 1/2 note incl. triplets and dotted), feedback.'],
      ['UNISON + LOCK', '1 .. 7', 'Voices in the unison stack; LOCK keeps their phases together.'],
      ['DRIFT', '0 .. 1', 'Slow analogue pitch drift per unison voice.'],
      ['SUB + SUB-2', '0 .. 1', 'Square sub oscillator one (or two) octaves down.'],
      ['P.ENV', '-1 .. 1', 'Mod envelope to pitch.'],
      ['FOLD, RATIO, FM', '', 'Wavefolder on the VCO and a sine FM pair (ratio and index).'],
      ['SPREAD', '0 .. 1', 'Stereo spread of the unison voices.'],
      ['BEND', '0 .. 24', 'Pitch-bend range in semitones.'],
      ['VELOCITY', '0 .. 1', 'How much velocity changes loudness.'],
      ['RESONATE', '0 .. 1', 'Nature resonator (chapter 5).'],
      ['STEREO', '0 .. 1', 'Random pan per note (on ObliqSonic: a random turn of each note round the listener).']])

# ============================================================== 7 matrix
H1('7  The pin matrix')
SHOT('sound_tMat.jpg', 'The MATRIX page: sources are rows (names in the spine), destinations are columns (abbreviations along the top). The page buttons sit in the gutter.')
P('Like the EMS Synthi\'s patch board, every source can be connected to every destination with a <b>pin</b>. There are 22 sources and 36 destinations '
  '(42 on ObliqSonic): 792 (924) pins. <b>Drag a pin up</b> and it turns green: a positive connection, more the further you drag. '
  '<b>Drag down</b> and it turns red: an inverted connection. In the centre (a plain hole) there is no connection. Hover a pin to see "source > destination". '
  'Any number of pins can be in at once (up to 128 are processed); per-voice sources such as velocity, key and the envelopes act separately on each note.')
H2('Sources (rows)')
TABLE([['Source', 'What it is'],
       ['LFO 1, LFO 2', 'The two LFOs (LFO page).'],
       ['MOD ENV, AMP ENV', 'The mod envelope and the amplitude envelope, per note.'],
       ['VELOCITY, KEY', 'Note velocity, and key position (0 at middle C, +-1 two octaves away).'],
       ['MOD WHEEL, AFTERTOUCH', 'MIDI CC 1 and channel pressure.'],
       ['RANDOM', 'A new random value for each note.'],
       ['CHAOS', 'A slowly wandering chaotic signal.'],
       ['NATURE', 'Envelope of the nature scene.'],
       ['FOLLOWER, OUTPUT', 'The audio followers (sampler, and the instrument\'s output).'],
       ['BOID X, BOID Y', 'Each note follows its own bird of the 8-boid flock (SWARM page).'],
       ['LORENZ X, Y, Z', 'The three axes of the Lorenz attractor.'],
       ['CC A, CC B, CC C, CC D', '<b>Incoming MIDI controllers.</b> The white number box beside each row chooses the CC number (drag or type, 0-127; defaults 74, 71, 21, 22). Any MIDI channel is accepted; the most recently moved one wins. Values are smoothed.']],
      [45, 125])
H2('Destinations (columns)')
TABLE([['Abbr.', 'Destination', 'Abbr.', 'Destination'],
       ['PCH', 'Pitch', 'P.OR', 'Polygon order'], ['CUT', 'Cutoff A', 'P.TE', 'Polygon teeth'],
       ['RES', 'Resonance A', 'P.RL', 'Polygon roll'], ['PW', 'Pulse width', 'P.OA', 'Polygon operator amount'],
       ['FLD', 'Fold', 'P.LV', 'Polygon level'], ['FM', 'FM amount', 'P.FD', 'Polygon fold'],
       ['SUB', 'Sub level', 'O.PA', 'Odessa partials'], ['NOI', 'Noise level', 'O.TL', 'Odessa tilt'],
       ['RSN', 'Nature resonator', 'O.TN', 'Odessa tension'], ['DTN', 'Detune', 'O.DN', 'Odessa density'],
       ['AMP', 'Amplitude', 'O.WP', 'Odessa warp'], ['PAN', 'Pan (ObliqSonic: turn round the listener)', 'O.PK', 'Odessa peaking'],
       ['L1R, L2R', 'LFO 1 / 2 rate (global)', 'O.LV', 'Odessa level'], ['DLY', 'Delay send', 'F.PS, F.SZ, F.LV', 'Keys layer position, size, level'],
       ['REV', 'Reverb send', 'B.CT', 'Cutoff B'], ['L.MD, L.MX, L.GN', 'Lester mode, A/B mix, gain', '', ''],
       ['S.DS, S.AZ, S.EL', 'ObliqSonic only: the note\'s distance, azimuth, elevation', 'S.SP, S.DV, S.AR', 'ObliqSonic only: spread, deviation, air']],
      [22, 63, 25, 60])
NOTE('Patches to try: LFO 1 > CUT (a slow sweep); VELOCITY > CUT (harder is brighter); CC A > O.DN (a knob on your controller sweeps the Odessa comb); '
     'BOID X > PAN or, on ObliqSonic, BOID X > S.DV and VELOCITY > S.AZ (each note flies off on its own path).')

# ============================================================== 8 swarm
H1('8  The swarm: boids and Lorenz on every parameter')
SHOT('sound_tSwarm.jpg', 'The SWARM page: the boids screen and the Lorenz attractor.')
P('Every continuous parameter of the instrument (92 on ObliqSonic) rides its own boid coordinate and its own axis of a Lorenz attractor. '
  'Two knobs in the bottom corners of the upper panel set how much: <b>BOIDS</b> (left) and <b>LORENZ</b> (right). At zero the instrument is completely '
  'still; a little of each makes it breathe; a lot makes it wander.')
CTRL([['SPEED, COHESION, SEPARATION, ALIGNMENT', '0 .. 1', 'The flock of 8 agents: how fast they fly, how strongly they gather, avoid each other and match each other\'s heading.'],
      ['RATE, SIGMA, RHO, BETA', '', 'The Lorenz attractor: speed and its three constants (10, 28, 2.667 is the classic butterfly).'],
      ['SOURCE, POLYGON, ODESSA, FILTER, FX, MOTION', 'on / off', 'Which sections of the instrument the swarm moves.'],
      ['V.BOIDS', 'on / off', 'Scales the per-note BOID X / Y matrix sources.']])

# ============================================================== 9 obliqsonic
H1('9  ObliqSonic: the spatial instrument')
SHOT('sonic_tSpace.jpg', 'ObliqSonic with the SPACE page open: the radar shows every point from above (front is up, left is left; bigger dots are higher).')
P('ObliqSonic is an <b>Ambisonics encoder that plays itself</b>. It receives MIDI like ObliqSound, makes the same sounds, and places them in '
  'a sphere of sound around the listener. It does not decode: it outputs the 16 Ambisonic channels for a decoder to turn into speakers or headphones.')
H2('The points')
TABLE([['Points', 'What they carry', 'Radar colour'],
       ['12 voice birds', 'Each note rides bird (slot mod 12): consecutive notes of a chord take neighbouring birds, so a chord spreads out. The note\'s own '
        'matrix destinations (S.DS, S.AZ, S.EL, S.SP, S.DV, S.AR, PAN) push it further, round, up, wider or astray.', 'pale green'],
       ['6 field copies', 'Six copies of the selected field recording play at once, <b>each with its own randomly wandering loop start and end</b>, '
        'each on its own path. (Choose squares 9-26 and raise SAMPLER.)', 'red'],
       ['2 FX returns', 'The delay and reverb (and the VCA INIT drone), as two wide sources.', 'amber'],
       ['2 nature points', 'The nature scene, left and right halves, as two broad sources.', 'amber']], [30, 115, 25])
H2('Motion')
P('All 22 points move continuously. <b>MODE</b> morphs between three motion systems, crossfading their positions:')
UL(['<b>FLOCK</b> (MODE 0): a three-dimensional flock. The birds keep their distance from each other, match headings and gather, half towards the '
    'flock\'s centre and half towards a leader circling the listener, so the group sweeps round you.',
    '<b>LORENZ</b> (MODE 1): every point has its own Lorenz attractor, with its constants and starting point <b>deviated</b> and its butterfly '
    'turned to its own heading. The points scatter over the whole sphere and trace chaotic loops.',
    '<b>GRAVITY</b> (MODE 2): three gravity wells orbit slowly; the points fall round them, slingshot and gather in clusters.',
    'In between, the two neighbouring systems are blended (the label under the radar shows FLOCK + LORENZ, LORENZ + GRAVITY ...). The swarm modulation '
    'can also move MODE itself.'])
H2('SPACE page controls')
CTRL([['MODE', '0 .. 2', 'Flock > Lorenz > Gravity.'],
      ['SPEED', '0 .. 1', 'How fast everything moves.'],
      ['DISTANCE', '1 .. 12 m', 'Radius of the scene. Far sources are quieter, later (Doppler), duller (air) and smaller.'],
      ['HEIGHT', '0 .. 1', 'Vertical extent: 0 keeps everything on the horizon, 1 uses the full sphere.'],
      ['DEVIATION', '0 .. 1', 'How far each point strays from its system: its own slow wander, its own Lorenz constants and heading.'],
      ['ROTATE', '-1 .. 1', 'Turns the whole scene round the listener, either way (up to one turn in 10 s).'],
      ['SPREAD', '0 .. 1', 'Size of the sources: turns the higher orders down, so each point becomes a broad, diffuse source.'],
      ['DOPPLER', '0 .. 1', 'Scales the propagation delay: points flying towards you rise in pitch, away fall.'],
      ['AIR', '0 .. 1', 'Air absorption: distant points lose their highs.'],
      ['GRAVITY', '0 .. 1', 'Strength of the gravity wells.'],
      ['COHESION', '0 .. 1', 'How tightly the flock gathers.'],
      ['FIELD SPLAY', '0 .. 1', 'Spreads the six field copies from their own centre: 0 one tight cloud, 1 all over the sphere.']])
H2('Distance model')
P('After the IEM RoomEncoder: each point has a propagation delay (distance / 343 m/s, scaled by DOPPLER), a 1/r level relative to a reference '
  'that follows DISTANCE (so turning DISTANCE up does not simply make everything quiet), and a low-pass for air absorption. Inside 1 m the higher orders '
  'fade so a source near your head spreads round you and gets up to 6 dB louder.')
H2('Output format')
TABLE([['', ''],
       ['Order', 'Third order: 16 channels'],
       ['Channel order', 'ACN (W, Y, Z, X, then the 2nd and 3rd order harmonics)'],
       ['Normalisation', 'SN3D (AmbiX). Set decoders to SN3D, order 3.'],
       ['Axes', 'x front, y left, z up (azimuth counter-clockwise, as in IEM and SPARTA)'],
       ['Output buses', '8 stereo buses = 16 channels. Hosts show 16 output pins; pin n goes to channel n.'],
       ['Limiter', 'A linked peak limiter driven by the omni (W) channel keeps the 16 channels in proportion.']], [40, 130], head=False)
P('The VU meters show a virtual cardioid pair (W+Y, W-Y), and the scopes and audio followers listen to the omni channel.')

# ============================================================== 10 routing
H1('10  Using ObliqSonic with IEM and SPARTA')
H2('REAPER (recommended)')
UL(['Insert ObliqSonic on a track. Track <b>Route</b> > <b>Track channels: 16</b>. Check the plug-in\'s pin connector (the "2 in 16 out" button in the FX window): outputs 1-16 should go to track channels 1-16 (the default).',
    'Headphones: insert <b>IEM BinauralDecoder</b> (order 3, SN3D) after ObliqSonic. Loudspeakers: <b>IEM AllRADecoder</b> or <b>SPARTA AmbiDEC</b>, with your speaker layout, and route the track to as many hardware outputs as speakers.',
    'Optional: <b>IEM SceneRotator</b> to rotate with a head tracker, <b>IEM FdnReverb</b> for an Ambisonic room, <b>IEM EnergyVisualizer</b> to see the energy.',
    'To mix several Ambisonic tracks, send them (16 channels) to one bus that holds the decoder.'])
H2('Other hosts')
P('Any host that can give an instrument 16 outputs and run a 16-channel decoder works (Bitwig, Nuendo, Pro Tools Ultimate in Ambisonics mode, Max, '
  'Plogue Bidule). Hosts that only use the first stereo bus will hear W and Y only: that is the omni channel plus left/right difference, a usable '
  'mid/side stereo, but not the full scene.')
NOTE('<b>Order and normalisation must match.</b> A decoder left at 1st order still works (it uses channels 1-4) but the image is blurrier. A decoder set '
     'to N3D will sound too bright and wide in the higher orders.')

# ============================================================== 11 presets / tips
H1('11  Presets, randomize and tips')
P('The 133 presets include the original Kia instrument sounds (with the new sections set up for them) and 32 new ones in the families XL, POLY, ODESSA, '
  'FIELD and LESTER. Older presets that used the earlier 8-slot mod matrix were converted into matrix pins. ObliqSonic ships with the same presets; '
  'the SPACE controls keep their current values when a preset from ObliqSound is loaded.')
UL(['<b>Slow evolving pad:</b> ODESSA up, PARTIALS 64, TILT 0.3, LFO 1 > O.DN, BOIDS and LORENZ at 0.2, REVERB 0.3.',
    '<b>Played field recording:</b> choose a recording square, KEYS 0.6, SIZE 0.05, KEYTRACK on, SCATTER 0.3: the recording becomes a granular instrument.',
    '<b>Spatial rain (ObliqSonic):</b> a water recording, SAMPLER 0.1, MODE 2 (gravity), FIELD SPLAY 1, DISTANCE 6, AIR 0.6.',
    '<b>Chord that explodes outward (ObliqSonic):</b> pin AMP ENV > S.DS (green) and RANDOM > S.AZ: each note starts close and flies off on its own bearing.'])

# ============================================================== 12 help
H1('12  The help window')
SHOT('sound_help.jpg', 'The help window, open on the VOICE topic.')
P('Both plug-ins and both desktop apps have a built-in help page. Press <b>Help</b>, beside the preset list at the top left, or <b>F1</b>. '
  'It opens over the panel as a small window with a list of topics on the left and the text on the right.')
CTRL([['Topics', '10 (11 on ObliqSonic)', 'START, CONTROLS, VOICE, SAMPLER, PAGES, LFO + DELAY, MATRIX, SWARM, SPACE (ObliqSonic only), PRESETS, APP + ABOUT. '
       'Click a topic, or use the up and down arrow keys.'],
      ['Manual (PDF)', 'button', 'Opens this manual, which is included inside each plug-in and app.'],
      ['Close', 'x, Esc', 'The x in the title bar, the Esc key, F1 again, or a click anywhere outside the window.']])
P('The instrument keeps playing while help is open, from MIDI and from the computer keyboard, so you can read about a control and hear it. '
  'The controls under the window cannot be moved until it is closed.')
NOTE('<b>Two questions the help answers first.</b> The amp <b>ADSR</b> is the four small knobs A D S R on the right wing under FILTER B (AMP ENV); '
     'the filter envelope is the same four on the left wing. The <b>delay time and feedback</b> are on the LFO page, bottom left, under FOLLOW / DELAY.')

# ============================================================== 13 desktop app
H1('13  The desktop app')
P('<b>ObliqSound.app</b> and <b>ObliqSonic.app</b> (in /Applications) are the instruments on their own, with no DAW.')
CTRL([['Options (top left)', '', 'Audio output, sample rate, buffer size and MIDI inputs. Every MIDI input is turned on at start, and new devices are picked up when plugged in.'],
      ['Computer keyboard', '', 'Plays notes (below). Click the panel first so it has the keyboard.'],
      ['Help', 'F1', 'The same help window as in the plug-ins (chapter 12).'],
      ['ObliqSonic: output', 'size list', 'The size list at the top right also chooses the output: <b>stereo</b> (a decode to two virtual cardioids, the default in the app) '
       'or <b>16-channel Ambisonics</b> for an interface or virtual device with 16 outputs.']])
TABLE([['Keys', 'Notes'],
       ['A  W  S  E  D  F  T  G  Y  H  U  J  K  O  L  P  ;  \'', 'C  C#  D  D#  E  F  F#  G  G#  A  A#  B  C  C#  D  D#  E  F'],
       ['Z / X', 'Octave down / up'],
       ['C / V', 'Velocity down / up (steps of 20, starts at 100)']], [70, 100])
P('The keys are ignored while Command is held.')

# ============================================================== 13 tech
H1('14  Technical reference')
TABLE([['', ''],
       ['Version', '2.1'],
       ['Engine', 'scsynth, the SuperCollider synthesis server (3.13), embedded in the plug-in and run in the host\'s audio callback. Both ObliqSound and ObliqSonic use it for all synthesis and sample playback; there is no other sound engine'],
       ['Custom UGens', 'Morphing zero-delay state-variable filter with drive and comb; 2x oversampled polygon oscillator; 128-partial additive bank; third-order Ambisonics encoder with distance'],
       ['Modulation', 'Computed in C++ once per 64 samples (envelopes, LFOs, pin matrix, swarm, motion) and written straight to the server\'s control buses; filter cutoff is smoothed per sample'],
       ['Polyphony', '16 voices with oldest-note stealing; a held VCA INIT chord keeps at most 8 notes'],
       ['Output stage', 'Look-ahead limiter, then 16-bit quantisation with dither'],
       ['Field recordings', '18 loops, 8 s, 16-bit stereo WAV, level-matched'],
       ['Swarm', '8 boids + Lorenz attractor moving the timbre parameters (never pitch, tuning, playback speed or levels)'],
       ['Matrix', '22 sources x 36 destinations (ObliqSound), x 42 (ObliqSonic); up to 128 active pins'],
       ['MIDI', 'Notes, velocity, pitch bend, mod wheel, channel pressure, any 4 CCs (any channel)'],
       ['ObliqSound output', 'Stereo'],
       ['ObliqSonic output', '16 channels, 3rd-order Ambisonics, ACN / SN3D; 22 moving point sources'],
       ['Formats', 'VST3, Audio Unit, desktop app; Apple silicon and Intel']], [40, 130], head=False)

H1('15  Troubleshooting')
TABLE([['Problem', 'What to do'],
       ['ObliqSonic sounds only in stereo or from one side', 'The track has fewer than 16 channels, or the decoder is missing. Set Track channels: 16 and insert a decoder at order 3, SN3D.'],
       ['ObliqSonic image is blurred or too bright', 'Check the decoder\'s order (3) and normalisation (SN3D).'],
       ['Crackles', 'Raise the host\'s buffer size (256 or 512).'],
       ['A CC does nothing', 'Check the number box in the matrix spine matches the CC your controller sends, and that a pin in that row is pulled up or down.'],
       ['Stuck notes', 'Send MIDI all-notes-off (CC 123), or play and release the note again.'],
       ['The bed is silent', 'SAMPLER is at 0, or a nature square is chosen with a very low level. Randomize always picks a square and an audible level.']],
      [55, 115])

# keep a heading on the same page as the screenshot that follows it
merged = []
for f in story:
    if isinstance(f, KeepTogether) and merged and isinstance(merged[-1], Paragraph) and getattr(merged[-1], 'toc', None):
        h = merged.pop()
        f = KeepTogether([h] + list(f._content))
    merged.append(f)
story[:] = merged
doc.multiBuild(story)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
