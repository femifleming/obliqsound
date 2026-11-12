// The built-in help: topics shown by the Help button (or F1) in the plug-ins and the desktop apps.
// Lines starting with "# " are headings; everything else is body text.
#pragma once
#include <juce_core/juce_core.h>

struct HelpTopic { const char* title; const char* body; bool sonicOnly; };

static const HelpTopic kHelp[] = {
{ "START",
  "# Playing\n"
  "Play from a MIDI keyboard, from the host's MIDI track, or from the computer keyboard (click the panel first):\n"
  "A W S E D F T G Y H U J K O L P ; '  are the notes from C upward.  Z / X move an octave down / up.  C / V lower / raise the velocity.\n"
  "Up to 16 notes sound at once; a 17th replaces the oldest.\n"
  "# The panel\n"
  "The upper half is always there: the oscillator in the middle, FILTER A and its envelope on the left wing, FILTER B and the AMP ENV on the right wing, "
  "the MIXER on the left shoulder and the OUTPUT section on the right, and the sampler's fan of squares in the centre.\n"
  "The lower half is a page. Choose it with the row of lights under the display: POLYGON, ODESSA, LESTER, LFO, MATRIX, SWARM (and SPACE on ObliqSonic).\n"
  "# First steps\n"
  "Pick a preset from the white list at the top left, or press Randomize.\n"
  "Turn CUTOFF A and RES for the tone, the A D S R knobs for the shape of the note.\n"
  "Click a square in the fan and raise SAMPLER to bring in a nature scene or a field recording.\n"
  "# This window\n"
  "Help or F1 opens it, Esc or a click outside closes it. The notes keep playing while it is open.", false },

{ "CONTROLS",
  "# Knobs, sliders and number boxes\n"
  "Drag up or down to turn.\n"
  "Hold Shift while dragging for fine steps.\n"
  "Double-click to return to the default value.\n"
  "The mouse wheel also turns the control under the pointer.\n"
  "# Switches and lights\n"
  "Click to switch. Lights that belong together (the waveform, the octave, the sampler squares, the pages) work as one selector.\n"
  "# Lists\n"
  "Click a white box with a small arrow to open its list.\n"
  "# Header\n"
  "Preset list: recalls a preset (the factory sounds and your own).\n"
  "Save: stores the current sound under a name you type.  Remove: deletes the chosen preset if it is one of yours.\n"
  "Randomize: rolls a new sound, including a random sampler square.\n"
  "Size (50 - 200 %): scales the window. 100 % and 200 % are the sharpest.\n"
  "# The background\n"
  "The green landscape drifts all the time and flows into a new shape when you change page. It is only a picture: it does not change the sound.", false },

{ "VOICE",
  "# Oscillator (centre)\n"
  "PITCH and FINE tune the whole instrument. WAVE chooses triangle, square, saw or sine. -1 / 0 / +1 set the octave. "
  "P.WIDTH is the pulse width, DETUNE spreads the unison stack, VIBRATO is LFO 2 on pitch.\n"
  "# Mixer (left shoulder)\n"
  "SAMPLER: the ambient bed.  KEYS: the recording played from the keyboard.  VCO, NOISE, POLYGON, ODESSA: the four synthesis layers. "
  "A layer at 0 is not computed.\n"
  "# Filters (wings)\n"
  "Two morphing filters, A on the left and B on the right. CUTOFF, RES, MODE (low-pass > band-pass > high-pass > notch > comb) and DRIVE. "
  "ENV AMT sets how far the filter envelope opens CUTOFF A. How A and B are joined is on the LESTER page.\n"
  "# Envelopes: where the ADSR is\n"
  "AMP ENV (loudness): the four small knobs A D S R on the right wing, under FILTER B.\n"
  "FILTER ENV: the four knobs A D S R on the left wing, under FILTER A.\n"
  "A third one, the mod envelope (ATTACK / DECAY), is on the LFO page.\n"
  "VCA INIT (right wing): a drone. The last chord keeps sounding at this level after you let go.\n"
  "# Output (right shoulder)\n"
  "CHORUS, TONE (colour of the noise), SPACE (reverb size), REVERB, OUTPUT (level; 3 is unity) and DRIVE.", false },

{ "SAMPLER",
  "# The fan of squares\n"
  "The 26 squares in the centre choose what the sampler plays. They are numbered in Ge'ez (Ethiopic) numerals; the display under the fan shows the current one.\n"
  "Squares 1 - 8: nature scenes, synthesized live (wind, birds, beach, geyser, forest, water, thunder, night).\n"
  "Squares 9 - 26: field recordings (8-second, 16-bit loops).\n"
  "# The bed\n"
  "SAMPLER (mixer) is the level of the chosen square as a continuous background. The loop's start and end points slide slowly all the time, "
  "so a recording never repeats exactly. SPEED sets its playback rate, REVERSE plays it backwards.\n"
  "# The keys layer\n"
  "KEYS (mixer) plays the recording from the keyboard: each note loops a small piece of it.\n"
  "PITCH transposes it. POSITION is where in the recording the loop sits. SIZE is the loop length, from a grain to the whole file. "
  "SCATTER starts each note at a random place near POSITION. KEYTRACK on: the keys play it chromatically.\n"
  "GLIDE (next to them) is portamento for the whole voice.\n"
  "# Followers and the resonator\n"
  "The sampler's loudness is a modulation source (FOLLOWER and NATURE in the matrix); F.ATTACK, F.RELEASE and F.GAIN on the LFO page shape it.\n"
  "RESONATE (LFO page) lets the nature scene ring at the pitch of each note.", false },

{ "PAGES",
  "# POLYGON\n"
  "An oscillator that traces a polygon. ORDER is the number of sides, TEETH makes it a star, ROLL turns it, 1:N and AMT add a phase-modulation operator. "
  "Each slider has a jack: the list under it chooses a modulation source and the small knob above sets how much. "
  "FM IN, FOLD, SLEW, WIDTH, SKEW and SPIN are at the sides. The screen draws the shape.\n"
  "# ODESSA\n"
  "An additive oscillator with up to 128 partials. PARTIALS, TILT (dark to bright), TENSION (stretches the series), "
  "DENSITY, WARP and PEAKING (a comb across the spectrum), BANK and FACTOR (two interleaved banks), the eight gates, "
  "and HEL CHORD, which stacks 1, 3 or 5 voices into a chord.\n"
  "# LESTER\n"
  "The two filters in depth. The link list joins them: off (side by side), A ctl (B follows A), series, 4pole, or stereo. "
  "A MIX B balances them. Each filter has three CV inputs: a source, a destination and an amount. RANDOMIZE rolls both filters.\n"
  "# The others\n"
  "LFO, MATRIX and SWARM have their own topics in the list on the left.", false },

{ "LFO + DELAY",
  "# LFO 1 and LFO 2\n"
  "RATE, SHAPE (sine, triangle, saw, square, sample & hold, smooth random) and SYNC to the host tempo. The two scopes show them. "
  "They do nothing until you connect them: in the MATRIX, in a POLYGON jack, or in a LESTER CV input (VIBRATO is LFO 2 on pitch).\n"
  "# Mod envelope\n"
  "ATTACK and DECAY: a third envelope for modulation. P.ENV sends it to pitch.\n"
  "# Delay: where time and feedback are\n"
  "Bottom left of the LFO page, under FOLLOW / DELAY:\n"
  "DELAY is the amount, TIME the delay time in note values of the host tempo (1/32 to 1/2, with triplets and dotted), FEEDBACK the number of repeats. "
  "It is a ping-pong delay and comes before the reverb.\n"
  "# Followers\n"
  "F.ATTACK, F.RELEASE and F.GAIN set how the audio followers respond.\n"
  "# Voice character\n"
  "UNISON (1 - 7 voices) with LOCK, DRIFT, SUB and SUB-2, FOLD, RATIO and FM, SPREAD, BEND (pitch-bend range), VELOCITY, RESONATE and STEREO.", false },

{ "MATRIX",
  "# The pin board\n"
  "Rows are sources, columns are destinations. Where a row and a column cross there is a pin.\n"
  "Drag a pin up: it turns green, a positive connection, stronger the further you drag.\n"
  "Drag it down: it turns red, an inverted connection.\n"
  "Double-click a pin to pull it out. Hover over one to read \"source > destination\".\n"
  "Any number of pins can be in at once.\n"
  "# Sources\n"
  "LFO 1, LFO 2, MOD ENV, AMP ENV, VELOCITY, KEY, MOD WHEEL, AFTERTOUCH, RANDOM (new for each note), CHAOS, NATURE, FOLLOWER, OUTPUT, "
  "BOID X / Y, LORENZ X / Y / Z and CC A - D.\n"
  "# MIDI controllers\n"
  "The four CC rows listen to incoming MIDI controllers. The white number box beside each row is the CC number (0 - 127; drag it). "
  "Any MIDI channel is accepted.\n"
  "# Destinations\n"
  "Pitch, cutoff, resonance, pulse width, fold, FM, sub, noise, resonator, detune, amplitude, pan, LFO rates, delay and reverb sends, "
  "the Lester, polygon and Odessa controls, and the keys layer. On ObliqSonic also each note's distance, azimuth, elevation, spread, deviation and air.\n"
  "# Try\n"
  "LFO 1 > CUT for a slow sweep.  VELOCITY > CUT so harder is brighter.  CC A > O.DN to sweep the Odessa comb from a controller.", false },

{ "SWARM",
  "# What it is\n"
  "A flock of 8 boids and a Lorenz attractor that can gently move every continuous control of the instrument at once. "
  "It never touches pitch, tuning, playback speed or levels.\n"
  "# How much\n"
  "Two knobs in the bottom corners of the upper panel: BOIDS (left) and LORENZ (right). At 0 the sound stands still; "
  "a little makes it breathe; a lot makes it wander.\n"
  "# The SWARM page\n"
  "SPEED, COHESION, SEPARATION, ALIGNMENT: how the flock flies.\n"
  "RATE, SIGMA, RHO, BETA: the Lorenz attractor (10, 28, 2.667 is the classic butterfly).\n"
  "SOURCE, POLYGON, ODESSA, FILTER, FX, MOTION: which sections the swarm is allowed to move.\n"
  "V.BOIDS scales the per-note BOID X / Y sources of the matrix.\n"
  "The two screens show the birds and the attractor.", false },

{ "SPACE",
  "# A spatial sound source\n"
  "ObliqSonic sends 16 channels of third-order Ambisonics (ACN order, SN3D normalisation), the format of the IEM Plug-in Suite and SPARTA. "
  "It does not decode: put a decoder after it (IEM BinauralDecoder for headphones, IEM AllRADecoder or SPARTA AmbiDEC for loudspeakers), set to order 3, SN3D.\n"
  "In REAPER: set the track to 16 channels (Route > Track channels).\n"
  "The desktop app plays a stereo decode by default; the size list at the top right switches between stereo and 16 channels.\n"
  "# The points\n"
  "22 points fly round the listener: 12 for the notes, 6 copies of the field recording (each with its own wandering loop), "
  "2 for the delay and reverb, 2 for the nature scene. The radar shows them from above; bigger dots are higher.\n"
  "# The SPACE page\n"
  "MODE morphs the motion: flock > Lorenz > gravity wells.\n"
  "SPEED, DISTANCE (radius of the scene), HEIGHT, DEVIATION (how far each point strays), ROTATE (turns the whole scene), "
  "SPREAD (size of the sources), DOPPLER, AIR (far sounds get duller), GRAVITY, COHESION and FIELD SPLAY (spreads the six field copies).\n"
  "# Per note\n"
  "The matrix columns S.DS, S.AZ, S.EL, S.SP, S.DV and S.AR move each note on its own.", true },

{ "PRESETS",
  "# Presets\n"
  "The white list at the top left holds the factory presets and your own.\n"
  "Save asks for a name and stores the sound: every control, the matrix pins and the CC numbers.\n"
  "Remove deletes the chosen preset if it is one of yours.\n"
  "Your presets are kept in presets.json in your application-data folder, under the instrument's name (macOS: ~/Library/Application Support, Windows: AppData/Roaming, Linux: ~/.config).\n"
  "In a host, the sound is also saved with the project.\n"
  "# Randomize\n"
  "Rolls the filters, envelopes, oscillators, effects and the sampler window, and picks a random sampler square at an audible level. "
  "On ObliqSonic it also rolls the motion. The RANDOMIZE light on the LESTER page rolls only the filters.\n"
  "# Ideas\n"
  "Slow pad: ODESSA up, PARTIALS 64, TILT 0.3, LFO 1 > O.DN, BOIDS and LORENZ at 0.2, REVERB 0.3.\n"
  "Played recording: choose a recording square, KEYS 0.6, SIZE 0.05, KEYTRACK on, SCATTER 0.3.\n"
  "Drone: play a chord, raise VCA INIT, then move the filters over it.", false },

{ "APP + ABOUT",
  "# The desktop app\n"
  "Options (top left of the window) opens the audio and MIDI settings: output device, sample rate, buffer size. "
  "Every MIDI input is switched on automatically, including devices you plug in later.\n"
  "The app remembers the sound and the devices.\n"
  "# If something is wrong\n"
  "Crackles: raise the buffer size (256 or 512).\n"
  "No sound: check OUTPUT, the mixer levels and CUTOFF A; in the app check Options > output device.\n"
  "A stuck note: play and release it again, or send all-notes-off.\n"
  "A CC does nothing: the number box of its matrix row must match the controller, and a pin in that row must be pulled up or down.\n"
  "ObliqSonic sounds flat: the track needs 16 channels and a decoder at order 3, SN3D.\n"
  "# About\n"
  "Version 2.2. The sound is made by SuperCollider's synthesis server (scsynth), built into the plug-in, with custom filter, polygon, additive "
  "and Ambisonics units. Nothing else needs to be installed. 16 voices, 16-bit output stage.\n"
  "# More\n"
  "The Manual button below opens the full owner's manual (PDF). Source and downloads: github.com/femifleming/obliqsound", false },
};
