#!/usr/bin/env python3
"""Request log: everything the author asked for, in order -> manual/ObliqSound_Request_Log.pdf"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = ROOT + 'manual/ObliqSound_Request_Log.pdf'
pdfmetrics.registerFont(TTFont('Tahoma-Bold', ROOT + 'src/Tahoma Bold.ttf'))
SAGE = colors.HexColor('#73AE8A'); SAGE_L = colors.HexColor('#E3EFE7'); SAGE_D = colors.HexColor('#3E6B50')
INK = colors.HexColor('#08160E'); GREY = colors.HexColor('#5B6B61')
S = {
    'title': ParagraphStyle('t', fontName='Tahoma-Bold', fontSize=22, leading=26, textColor=SAGE_D, spaceAfter=4),
    'sub': ParagraphStyle('s', fontName='Helvetica', fontSize=10, leading=14, textColor=GREY, spaceAfter=10),
    'h1': ParagraphStyle('h1', fontName='Tahoma-Bold', fontSize=14, leading=18, textColor=SAGE_D, spaceBefore=12, spaceAfter=6),
    'p': ParagraphStyle('p', fontName='Helvetica', fontSize=9.4, leading=13, textColor=INK, spaceAfter=5),
    'c': ParagraphStyle('c', fontName='Helvetica', fontSize=8.3, leading=10.8, textColor=INK),
    'q': ParagraphStyle('q', fontName='Helvetica-Oblique', fontSize=8.3, leading=10.8, textColor=INK),
    'b': ParagraphStyle('b', fontName='Tahoma-Bold', fontSize=7.8, leading=10.4, textColor=INK),
    'hd': ParagraphStyle('hd', fontName='Tahoma-Bold', fontSize=8, leading=10.4, textColor=colors.white),
}

def esc(t): return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# (phase title, [(date, time UTC, request in the author's words, what was done, status)])
DONE, CHG, OPEN, INFO, DROP = 'Done', 'Done, later changed', 'Partly', 'Answered', 'Withdrawn'
PHASES = [
 ('1  From the Kia instrument to a new synthesizer', [
  ('10 Nov', '02:31', '[the Kia instrument VST3] make this vst sound way better, make it way cooler with way more modulation and make it way more complex and interesting. keep the same aesthetic, dont subtract from it just add too it.',
   'Extended the instrument around its original controls: a fuller oscillator (unison, sub, FM, wavefolder), two LFOs, a mod envelope, modulation routing and effects. Nothing was removed.', DONE),
  ('10 Nov', '03:12', 'remove the keyboard from the visual. i need it even more complex [image] like this module. i dont want it modular but i like this idea a lot, implement it into this synth. [link: E-RM Polygogo]',
   'Removed the on-screen keyboard. Added the POLYGON oscillator (order, teeth, roll, phase-modulation operator, fold, jacks with attenuverters) as a built-in section, not a patchable module.', DONE),
  ('10 Nov', '03:22', 'now also add all of the ideas from this [link: XAOC Devices Odessa] and add these also as stock audio. have a follower of the audio also be a modulation source for things. [folder of the author\'s field recordings] you can convert them to 16 bit wav and make smaller loops of somehwere in the middel of all the recordings so its not super long.',
   'Added the ODESSA additive oscillator (up to 128 partials, tilt, tension, density, warp, peaking, banks, chord mode). Cut the 18 field recordings into short 16-bit loops taken from the middle of each file and added them as stock audio. Added an audio follower as a modulation source.', DONE),
  ('10 Nov', '04:00', 'the field recordings need to go where the squares of feild recordings already are, not a seperate style, and redesin the whole vst to make it perfectly symetrical. also make sure all engines work polyphonically.',
   'Moved the recordings into the existing sampler squares, redesigned the panel symmetrically, and made every engine polyphonic.', DONE),
  ('10 Nov', '04:30', 'i want boid and lorenz curve modulation for every parameter, make the ui way more compact like a eurorack module would be. give me real looking knobs and switches. its also not too symettrical looking i want it mirror symetrrical, you can place thigns wherever you need them to go for it to perfecr mirror, aksi maekt the background an aluminum panel',
   'Added the swarm (8 boids and a Lorenz attractor on every continuous parameter), rendered knobs and switches, a compact mirror-symmetric layout and an aluminium panel. The aluminium panel was replaced two requests later.', CHG),
  ('10 Nov', '04:56', 'install it', 'Installed on the Mac.', DONE),
 ]),
 ('2  The look: organic, mirrored, 90s render, topographic', [
  ('10 Nov', '04:58', 'i want the mirror to be more of an organic layout, not so grid and metal panel/old synth looking.',
   'Replaced the grid and the metal panel with an organic layout: controls on arcs and curves, mirrored about the centre line.', DONE),
  ('10 Nov', '05:10', '[image] call it obliqesound, use this logo and color [image] make it this aesthetic but with the color i just gave you instead of orange.',
   'Named the instrument, used the supplied logo and its sage green (#73AE8A) in the look of the reference image.', DONE),
  ('10 Nov', '05:26', 'make vst and vst3', 'Built both formats at the time. Since version 2 the formats are VST3, Audio Unit and desktop app (see the open points).', CHG),
  ('10 Nov', '05:29', 'go back to it looking organic layout and mirrored, use that logo and color, and use [image] this and [image] this aesthetic of old 90s render plugins, use old style renderings and that pixel quality of windows 2000. but make it mirror synetrical and have an organic layout.',
   'Returned to the organic mirrored layout and drew it as a late-90s rendered plug-in at Windows 2000 pixel quality, with the logo and colour.', DONE),
  ('10 Nov', '05:38', 'it looks beautiful. this is perfect, but add more and more layers of green around the main organic shape, almost like its topagraphical. make the outer layers darker and darker. when i switch modes, have the shape morph into the next shape liee the topogrpahy is moving. this resolution and pixel qualty is perfect.',
   'Added topographic rings that darken outward, and a rendered morph of the landscape from one page\'s shape to the next.', DONE),
  ('10 Nov', '05:49', 'i want the background to also to always be kind of morphing slowly randomly. also make it a desktop app. the motion and lfo mapping tab i want to be a a huge big pin matrix like the ems synthi.',
   'The landscape now drifts all the time. Built a desktop app. Replaced the mapping tab with a pin matrix of every source against every destination.', DONE),
  ('10 Nov', '06:17', 'i liked where the different page buttons were before, move them from the bottom.',
   'Moved the page buttons back into the arc under the display.', DONE),
  ('10 Nov', '06:22', 'replace all the names of the field recordings with etheopian numerals.',
   'The sampler squares and the display are numbered in Ge\'ez (Ethiopic) numerals.', DONE),
  ('10 Nov', '07:46', 'the morphoing of the background seems to just crossfade between images, it was really dynamically moving and morphoing before, go back to it looking like that.',
   'Dropped the crossfade and rendered real in-between shapes again.', DONE),
  ('10 Nov', 'c. 07:50', 'that seems to just have it do it around the outside shape, it was morphing more of the entire shape more dramatically, and symetrically before.',
   'Re-rendered the idle motion so the whole landscape moves, with mirrored bulges and lakes (120 shapes per page).', DONE),
 ]),
 ('3  Sampler behaviour', [
  ('10 Nov', '06:06', 'randomize also needs to choose a random feild recording',
   'Randomize also picks a sampler square, at an audible level.', DONE),
  ('10 Nov', '06:09', 'for the field recordings, the start and end point are contiinuously always slowly slew-ly changing. slowly at the same speed of the background. from what you opened, it seems the frame rate is super low too. make it high 30fps',
   'The loop start and end points of the recordings drift slowly all the time, on the same clock as the background. The panel redraws at 30 frames a second.', DONE),
 ]),
 ('4  ObliqSonic, the spatial twin', [
  ('10 Nov', '06:15', 'make a multichannel iem/sparta encoder instruemnt deviated flocking boid lorenz gravity moved version of this vst called obliqsonic, look at what youve done for mellyloon plugin and the other spatial plugin, the only difference is this is a sound source that receives midi. in the midi pin matrix, also let me map incoming midi cc to things.',
   'Built ObliqSonic: the same instrument as a 16-channel third-order Ambisonics source (ACN / SN3D) whose points move on a flock, deviated Lorenz attractors or gravity wells. Added four MIDI CC rows to the pin matrix of both instruments.', DONE),
  ('10 Nov', '06:15', 'but only do that when youre done with this', 'Started ObliqSonic after the ObliqSound work in progress was finished.', DONE),
  ('10 Nov', '06:20', 'in the spatial audio version, when youre ready for it, the feild reocrdings are copied and moving around, each one with its own random modulators for start and end point.',
   'ObliqSonic plays six copies of the chosen recording as six moving points, each with its own wandering loop start and end.', DONE),
 ]),
 ('5  Manual, GitHub, names, installing', [
  ('10 Nov', '07:34', 'make a comprehensive manual pdf for both vsts when you are done', 'Wrote the owner\'s manual (PDF) for both instruments.', DONE),
  ('10 Nov', '08:07', 'i need to close my mac and migrate, can i do that? i will be back', 'Answered; work resumed afterwards.', INFO),
  ('10 Nov', '08:42', 'for all vst plugins you have ehlped me build, in all of the github repo readmes add a human contributions section.',
   'Added a "Human contributions" section to the README of all five plug-in repositories.', DONE),
  ('10 Nov', '08:50', 'mak obliqesound and obliqsonic both desktop apps as well and push that. are they?', 'Both are desktop apps; pushed.', DONE),
  ('10 Nov', '08:51', 'open the pdf for me also', 'Opened the manual.', DONE),
  ('10 Nov', '08:59', 'public everyhting but dont hace any kia logos. link to the original kia plgin in the readme  /  Yes, push all five',
   'Made the repository public with no Kia logos and a link to the original Kia instrument in the README; pushed all five repositories.', DONE),
  ('10 Nov', '09:12', 'install the latest version on my computer and delete the old verson, on my verion on my computer the displays seem broken, cna you check that?',
   'Installed the latest build and removed the old one. Fixed the LFO and Lorenz displays and drew new waveform icons.', DONE),
  ('10 Nov', '09:18', 'when youte done push the new version', 'Pushed.', DONE),
  ('10 Nov', '09:53', 'delete all that are not the latest ones and move the latest one to my applications folder', 'Removed the older copies; the latest apps are in /Applications.', DONE),
  ('10 Nov', '09:55', 'Its called Obliqsound and Obliqsonic not kia instrument  /  rename it all to ObliqSound and ObliqSonic',
   'Renamed everything to ObliqSound and ObliqSonic.', DONE),
  ('10 Nov', '10:05', 'i jsut wanted to change the name of the vst so i can find it under ObliqSound and ObliqSonic it doesnt need to be complex  /  vst and the app*',
   'Kept it simple: the plug-ins and the apps carry the two names and are listed under them in a host.', DONE),
  ('10 Nov', '10:07', 'make vst and vst 3 for both', 'Built both formats for both instruments at the time (see the open points for version 2).', CHG),
  ('10 Nov', '19:05', 'update the github and remove all old versions from the github and from my computer',
   'Updated the repository, deleted the old releases, and removed the old versions and the original Kia instrument from the Mac.', DONE),
  ('10 Nov', '19:32', 'all \'!\' command you have permission to go ahead and run terminal commands youself', 'From then on the commands were run directly instead of being handed over.', DONE),
 ]),
 ('6  Sound quality and the move to SuperCollider', [
  ('10 Nov', '19:21', 'the audio seems to be seriously distorting and low quality, and some of the feield recordings are distorted, i think the original oners from the kia app. the program is super laggy and the gainstaging weird, its clipping on the output and doesnt sound polyphonic up to 16 voices.',
   'Fixed stuck voices, the distortion, the gain staging and the CPU load; 16 voices with oldest-note stealing; re-levelled the recordings.', DONE),
  ('10 Nov', '19:48', 'samples should be 16 bit wav instead of 24 bit', 'All samples are 16-bit WAV.', DONE),
  ('10 Nov', '20:00', 'install it on my mac and remove all old versions, when youre finished, open it', 'Installed, old versions removed, app opened.', DONE),
  ('10 Nov', '20:24', 'check obliqesonic as well. make both synth engines for both apps 16 bit. the app is still lagging and glitching hevily on my end when i send it a lot of midi notes.',
   'Checked ObliqSonic too and gave both engines a 16-bit output stage. The lag under dense MIDI was not fully cured in the Csound engine, which led to the next request.', OPEN),
  ('12 Nov', '07:20', 'dont use csound use a higher quality sound engine, something that makes sense. try using supercollider for the base.',
   'Version 2.0: a new engine on SuperCollider\'s synthesis server (scsynth) embedded in the plug-in, with custom filter, polygon, additive and Ambisonics units, and new plug-ins written with JUCE. A flood of 60 notes a second now costs about a quarter of one core where the old engine missed blocks.', DONE),
  ('12 Nov', '08:06', 'i dont think its receiving midi', 'Checked both apps with MIDI sent over the IAC bus: they receive it. The author confirmed.', INFO),
  ('12 Nov', '08:23', 'midi works. i dont see delay time and feedback anywhere, and wheres the adsr for the synth?',
   'Answered: the amp ADSR is on the right wing under FILTER B, the delay controls are on the LFO page. Both answers are now in the built-in help.', INFO),
 ]),
 ('7  Versions 2.1 and 2.2: help page, manual, this log, Windows and Linux', [
  ('12 Nov', '08:25', 'remove the sampler part entirely from both plugins but keep the aesthetic and design as similar as possible.  /  make sure both plugins are supercollider based on the synthesis side',
   'The sampler removal was withdrawn before any work was done (next line). Both plug-ins are SuperCollider-based: all synthesis and sample playback run in the embedded scsynth server, and no Csound is shipped.', DROP),
  ('12 Nov', '08:38', 'nevermind, dont remove the sampler part.', 'The sampler stays exactly as it was.', DONE),
  ('12 Nov', '09:00', 'keep the sampler part, push both of these to github. also update github woth a log of everything ive asked for breaked down in a pdf as a log. make sure you update the manual as well. also add a help page to the vst\'s and standalone desktop apps before you push to github.  /  push it all to github when youre done',
   'Added a Help button (and F1) to both plug-ins and both apps: a help window with ten topics (eleven on ObliqSonic) and a button that opens the manual. Updated the manual with a help chapter. Wrote this log. Pushed everything as version 2.1.', DONE),
  ('12 Nov', 'c. 09:25', 'make sure latest build of vsts and standalones work on mac windows and linux',
   'Version 2.2. The engine\'s audio driver was rewritten so one version serves all three systems, and the build was opened to Microsoft\'s compiler and GCC. Windows and Linux VST3s and desktop apps are now built and tested on GitHub\'s machines (a 16-voice engine test and pluginval: load, editor, audio, automation), and all pass. The Linux app was also run and looked at in a container. macOS was rebuilt, installed and validated.', DONE),
 ]),
]

OPEN_POINTS = [
 ['VST2', 'Asked for twice. The first (Csound / Cabbage) builds had it. Version 2 has VST3, Audio Unit and desktop apps only, because the VST2 SDK is no longer available.'],
 ['Odessa spectrum LEDs', 'The 12 LEDs on the ODESSA page are not animated in version 2.'],
 ['Polygon screen', 'The screen draws the shape from the knob positions, not from the audio.'],
 ['Presets', 'The 133 presets were carried over to the new engine by their values; they have not been re-voiced by ear.'],
 ['ObliqSonic in a decoder chain', 'The 16-channel output passes the format checks, but it has not been listened to through the IEM or SPARTA decoders in REAPER as part of this work.'],
 ['Windows and Linux by hand', 'The Windows and Linux builds pass the automated tests, but nobody has yet played them or heard them in a DAW on those systems. They are not code-signed, so Windows SmartScreen asks once.'],
 ['Delay and ADSR placement', 'An offer to move the delay controls to the main panel and relabel the envelopes was not taken up; nothing was changed.'],
]

def page(c, d):
    W, H = A4
    c.setStrokeColor(SAGE); c.setLineWidth(2); c.line(16 * mm, H - 13 * mm, W - 16 * mm, H - 13 * mm)
    c.setFont('Tahoma-Bold', 7.5); c.setFillColor(SAGE_D)
    c.drawString(16 * mm, H - 11 * mm, 'OBLIQSOUND  /  OBLIQSONIC'); c.drawRightString(W - 16 * mm, H - 11 * mm, 'REQUEST LOG')
    c.setFont('Helvetica', 8); c.setFillColor(GREY); c.drawCentredString(W / 2, 9 * mm, str(d.page))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=19 * mm, bottomMargin=16 * mm,
                        title='ObliqSound / ObliqSonic - Request log', author='ObliqSound')
st = [Paragraph('Request log', S['title']),
      Paragraph('ObliqSound and ObliqSonic  -  everything the author asked for, in order, and what came of it  -  10 to 12 November 2026', S['sub'])]
total = sum(len(e) for _, e in PHASES)
counts = {}
for _, es in PHASES:
    for e in es: counts[e[4]] = counts.get(e[4], 0) + 1
st.append(Paragraph(
    'ObliqSound and ObliqSonic were written with Claude Code (Anthropic) under the direction of their author. This log lists the author\'s '
    f'requests, {total} entries in seven groups. The requests are quoted as they were typed; attached pictures are marked [image], links are named, '
    'and a private folder path is replaced by a description. Related messages sent together share an entry, separated by a slash. Times are UTC.', S['p']))

st.append(Paragraph('Overview', S['h1']))
rows = [[Paragraph(x, S['hd']) for x in ('Group', 'Entries', 'Dates')]]
for t, es in PHASES:
    ds = sorted({e[0] for e in es}); rows.append([Paragraph(esc(t), S['c']), Paragraph(str(len(es)), S['c']), Paragraph(' - '.join([ds[0], ds[-1]]) if len(ds) > 1 else ds[0], S['c'])])
tb = Table(rows, colWidths=[120 * mm, 20 * mm, 38 * mm])
tb.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), SAGE_D), ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#C9D9CF')),
                        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
st += [tb, Spacer(1, 6)]
st.append(Paragraph('Outcome: ' + ',  '.join(f'<b>{counts[k]}</b> {k.lower()}' for k in (DONE, CHG, OPEN, INFO, DROP) if k in counts) + '.', S['p']))

COL = {DONE: SAGE_L, CHG: colors.HexColor('#F3EBCF'), OPEN: colors.HexColor('#F3EBCF'), INFO: colors.HexColor('#E6E9EE'), DROP: colors.HexColor('#EEDCDC')}
n = 0
for t, es in PHASES:
    st.append(Paragraph(esc(t), S['h1']))
    rows = [[Paragraph(x, S['hd']) for x in ('No.', 'When', 'Request', 'What was done', 'Status')]]
    style = [('BACKGROUND', (0, 0), (-1, 0), SAGE_D), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#C9D9CF')),
             ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    for d, tm, req, done, status in es:
        n += 1
        rows.append([Paragraph(str(n), S['b']), Paragraph(f'{d}<br/>{tm}', S['c']), Paragraph('"' + esc(req) + '"', S['q']), Paragraph(esc(done), S['c']), Paragraph(status, S['b'])])
        style.append(('BACKGROUND', (4, len(rows) - 1), (4, len(rows) - 1), COL[status]))
    tb = Table(rows, colWidths=[9 * mm, 15 * mm, 70 * mm, 64 * mm, 20 * mm], repeatRows=1)
    tb.setStyle(TableStyle(style)); st.append(tb)

st.append(Paragraph('Open points', S['h1']))
st.append(Paragraph('Things that were asked for and are not fully in the current version, or that have not been checked:', S['p']))
rows = [[Paragraph(a, S['b']), Paragraph(esc(b), S['c'])] for a, b in OPEN_POINTS]
tb = Table(rows, colWidths=[45 * mm, 133 * mm])
tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#C9D9CF')), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
st.append(tb)
doc.build(st, onFirstPage=page, onLaterPages=page)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB,', total, 'entries')
