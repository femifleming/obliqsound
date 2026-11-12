; =====================================================================
;  ObliqSound / ObliqSonic  -  open polyphonic engine
;  Follows every control of the instrument it grew from (same channels),
;  plus: 2 LFOs, mod envelope, 8-slot mod matrix, unison/detune/drift,
;  sub, FM, wavefolder, nature resonator, glide, chorus, drive,
;  ping-pong delay and a sized reverb.
; =====================================================================
ksmps  = 128
nchnls = @NCHNLS@
0dbfs  = 1
seed 0

massign 0, 1
pgmassign 0, 0
maxalloc 11, 40
gkNoteN init 0            ; running count of notes started (for voice stealing)

giSine ftgen 0, 0, 8192, 10, 1
giScL1 ftgen 0, 0, 256, -2, 0     ; scope histories (LFO 1, LFO 2, Lorenz x / y)
giScL2 ftgen 0, 0, 256, -2, 0
giScLX ftgen 0, 0, 256, -2, 0
giScLY ftgen 0, 0, 256, -2, 0

#ifdef SONIC
; =====================================================================
;  ObliqSonic: third-order Ambisonics encoder (16 ch, ACN / SN3D, the
;  IEM / SPARTA convention; x front, y left, z up). Every voice, every
;  copy of the field recording, the FX returns and the nature bed are
;  points flying round the listener on a flock / deviated Lorenz /
;  gravity motion system, each with distance delay (Doppler), 1/r and
;  air absorption, after the IEM RoomEncoder.
; =====================================================================
gaAmb[] init 16
giNP = 22                 ; 0-11 voice birds, 12-17 field copies, 18-19 fx, 20-21 nature
gkPX[] init 22
gkPY[] init 22
gkPZ[] init 22
gkTX[] init 22
gkTY[] init 22
gkTZ[] init 22
gkSpMode init 0.6
gkSpSpeed init 0.3
gkSpDist init 3
gkSpHeight init 0.5
gkSpDev init 0.3
gkSpRot init 0
gkSpSpread init 0.15
gkSpDopp init 0.5
gkSpAir init 0.4
gkSpGrav init 0.5
gkSpCoh init 0.5
gkSpFSplay init 0.6

; real spherical harmonics to 3rd order, ACN order, SN3D, from a unit vector
opcode SpSH, k[], kkkkkk
  kx, ky, kz, kw1, kw2, kw3 xin
  kG[] init 16
  kx2 = kx * kx
  ky2 = ky * ky
  kz2 = kz * kz
  kG[0] = 1
  kG[1] = ky * kw1
  kG[2] = kz * kw1
  kG[3] = kx * kw1
  kG[4] = 1.7320508 * kx * ky * kw2
  kG[5] = 1.7320508 * ky * kz * kw2
  kG[6] = 0.5 * (3 * kz2 - 1) * kw2
  kG[7] = 1.7320508 * kx * kz * kw2
  kG[8] = 0.8660254 * (kx2 - ky2) * kw2
  kG[9] = 0.7905694 * ky * (3 * kx2 - ky2) * kw3
  kG[10] = 3.8729833 * kx * ky * kz * kw3
  kG[11] = 0.6123724 * ky * (5 * kz2 - 1) * kw3
  kG[12] = 0.5 * kz * (5 * kz2 - 3) * kw3
  kG[13] = 0.6123724 * kx * (5 * kz2 - 1) * kw3
  kG[14] = 1.9364917 * kz * (kx2 - ky2) * kw3
  kG[15] = 0.7905694 * kx * (kx2 - 3 * ky2) * kw3
  xout kG
endop

; one point source: propagation delay (Doppler), 1/r, air absorption, then encode into gaAmb
opcode SpPoint, 0, akkkkk
  asig, kx, ky, kz, kspr, kair xin
  krad = sqrt(kx * kx + ky * ky + kz * kz)
  krad = max(krad, 0.0001)
  kdel = min(krad, 30) / 343 * 1000 * gkSpDopp
  adel interp kdel
  ad vdelay3 asig, adel, 100
  kcut = 20000 * exp(-min(krad, 40) * limit(kair, 0, 1) * 0.12)
  ad tone ad, kcut
  kref = 1 + (gkSpDist - 1) * 0.5
  kg = min(2, kref / max(krad, 0.5))
  knear limit krad, 0, 1                         ; inside 1 m the higher orders fade: the sound spreads round you
  ks limit kspr, 0, 1
  kw = knear * (1 - ks)
  kG[] SpSH kx / krad, ky / krad, kz / krad, kw, kw * kw, kw * kw * kw
  ki = 0
  while ki < 16 do
    gaAmb[ki] = gaAmb[ki] + ad * (kG[ki] * kg)
    ki += 1
  od
endop
#end

; ---- buses (cleared by the master) ----
gaVL init 0
gaVR init 0
gaDlyL init 0
gaDlyR init 0
gaRevL init 0
gaRevR init 0
gaNatL init 0
gaNatR init 0
gaNatPrev init 0

; ---- shared modulation state ----
gkL1 init 0
gkL2 init 0
gkChaos init 0
gkNatEnv init 0
gkWheel init 0
gkLastPitch init 48
gkMS[] init 8
gkMD[] init 8
gkMA[] init 8

; ---- parameters (written by the control instrument) ----
gkVCO init 0
gkTune init 1
gkOct init -24
gkWave init 3
gkPW init 0.5
gkLP init 6548
gkRes init 0.12
gkMod init 1
gkFA init 0.11
gkFD init 0.34
gkFS init 0.2
gkFR init 0.2
gkAA init 0.02
gkAD init 0.5
gkAS init 0.568
gkAR init 0.516
gkInit init 0
gkTone init 800
gkVol init 3
gkAmpVCO init 2
gkNoise init 0.341
gkRev init 0.126
gkSamp init 0.005
gkNatSel init 1
gkMeA init 0.005
gkMeD init 0.45
gkUni init 3
gkDetune init 0.18
gkSpread init 0.6
gkDrift init 0.3
gkSub init 0
gkFM init 0
gkFMRatio init 2
gkFold init 0
gkGlide init 0
gkResonate init 0
gkVelAmt init 0.5
gkChorus init 0.25
gkDrive init 0.12
gkDlyMix init 0.14
gkDlyTime init 6
gkDlyFb init 0.35
gkSpace init 0.5
gkBPM init 120
gkHeld init 0
gkPinS[] init 128
gkPinD[] init 128
gkPinA[] init 128
gkPinN init 0
gkLzX[] init 24
gkLzY[] init 24
gkCC[] init 4             ; the four MIDI CC rows of the matrix
; swarm modulation (boids + lorenz)
gkBoidX[] init 8
gkBoidY[] init 8
gkBVX[] init 8
gkBVY[] init 8
gkLorX init 0
gkLorY init 0
gkLorZ init 0
gkSwB[] init 6
gkSwL[] init 6
gkVStereo init 0.3
gkPEnv init 0
gkVib init 0
gkVuL init 0
gkVuR init 0
gkBendR init 2
gkScBV init 1
gkUniLock init 0
gkSub2 init 0
gkGen init 0
gkSlot init 0
gkKeyUp[] init 64
gkBend init 0
gkMWheel init 0
gkATouch init 0
gkTab init 1
; polygon oscillator
gkPTune init 0
gkPOrder init 4
gkPTeeth init 0
gkPRoll init 0
gkPRatio init 1
gkPAmt init 0
gkPFM init 0
gkPFold init 0
gkPLevel init 0.3
gkPWidth init 0.7
gkPSlew init 0.02
gkPSpin init 0
gkPSkew init 0
gkPCycle init 0
gkPRegular init 0
gkPSnap init 1
gkJS[] init 6
gkJA[] init 6
gaDispX init 0
; odessa
gkOTune init 0
gkOFine init 0
gkOSpread init 0.2
gkOVoices init 1
gkOChord init 1
gkOPart init 32
gkOTension init 0
gkOTilt init 0.5
gkOBank init 0
gkOFactor init 0
gkODens init 0
gkOWarp init 0
gkOPeak init 0.5
gkOFund init 0
gkOFundSq init 0
gkOLevel init 0
gkOWidth init 0.8
gkOG[] init 8
gkOCvS[] init 4
gkOCvA[] init 4
gaOdeL init 0
gaOdeR init 0
; chord intervals (Hel): one row of 5 voices per chord
giChords ftgen 0, 0, 64, -2, 0,0,0,0,0,  0,-12,12,-24,24,  0,-5,7,-12,19,  0,5,7,12,17,  0,4,7,12,16,  0,3,7,12,15,  0,4,7,11,14,  0,3,7,10,14,  0,7,14,16,19,  0,5,10,15,20,  0,1,2,-1,-2,  0,2,4,6,8
; field (stock audio)
gkFRec init 1
gkFBed init 0
gkFSpeed init 1
gkFRev init 0
gkFVoice init 0
gkFPitch init 0
gkFKey init 1
gkFPos init 0.3
giIdleStep init 1 / @IDLEFPS@   ; seconds per background frame (the loop drift follows the same clock)
gkLpA init 0.5
gkLpB init 0.5
gkFSize init 0.25
gkFScatter init 0.1
gkFTabL init 0
gkFTabR init 0
gkFLen init 8
gkFSrFix init 1
gkFNorm init 1
gkFAtt init 0.01
gkFRel init 0.25
gkFGain init 1
gkFollow init 0
gkOutEnv init 0
gaFieldL init 0
gaFieldR init 0
gaFieldRaw init 0
gaOutPrev init 0
giFLoaded[] init 64
giFTabL[] init 64
giFTabR[] init 64
giFLen[] init 64
; lester
gkAMode init 0
gkAGain init 0.5
gkBCut init 18000
gkBRes init 0.12
gkBMode init 0
gkBGain init 0.5
gkLink init 4
gkLMix init 1
gkLCvS[] init 6
gkLCvD[] init 6
gkLCvA[] init 6
gaDispY init 0
gaPrevX init 0
gaPrevY init 0

; ---------------------------------------------------------------------
;  LFO: 1 sine 2 triangle 3 saw 4 square 5 sample&hold 6 smooth random
; ---------------------------------------------------------------------
opcode KXLfo, k, kk
  krate, kshape xin
  kph init 0
  kold init 0
  knew init 0
  kph += krate * ksmps / sr
  if kph >= 1 then
    kph -= int(kph)
    kold = knew
    knew random -1, 1
  endif
  ksh = round(kshape)
  if ksh == 1 then
    kout = sin(2 * $M_PI * kph)
  elseif ksh == 2 then
    kout = 1 - 4 * abs(kph - 0.5)
  elseif ksh == 3 then
    kout = 2 * kph - 1
  elseif ksh == 4 then
    kout = (kph < 0.5 ? 1 : -1)
  elseif ksh == 5 then
    kout = knew
  else
    kout = kold + (knew - kold) * (0.5 - 0.5 * cos($M_PI * kph))
  endif
  xout kout
endop

; tempo-sync: quantise a rate in Hz to the nearest musical division
opcode KXSync, k, kk
  krate, kbpm xin
  kbps = kbpm / 60
  kbest = 1
  kerr = 1000
  ki = 0
  while ki < 11 do
    kdiv tab ki, 900          ; beats per cycle
    kf = kbps / kdiv
    ke = abs(log(kf / krate))
    if ke < kerr then
      kerr = ke
      kbest = kf
    endif
    ki += 1
  od
  xout kbest
endop
; ---------------------------------------------------------------------
;  Polygonal oscillator (continuous-order polygon traced in X/Y)
;  order  : number of sides (fractional ok)    teeth : star-ness
;  roll   : rotation (turns)  ratio/amt : phase-mod operator  cycle : precession
; ---------------------------------------------------------------------
opcode KXPoly, aa, akkkkkkk
  acps, korder, kteeth, kroll, kratio, kamt, kcycle, kskew xin
  aph phasor acps
  aop phasor acps * kratio
  ath = aph + kamt * sin(2 * $M_PI * aop) * 0.3
  kn limit korder, 2.05, 32
  kpin = $M_PI / kn
  kTmax = max(0, $M_PI / 2 - kpin - 0.07)
  kT = kteeth * kTmax
  afr = ath * kn
  afr = afr - floor(afr)
  aden = cos(2 * kpin * afr - kpin + kT)
  aden limit aden, 0.04, 1
  aP = cos(kpin + kT) / aden
  aang = 2 * $M_PI * (ath + kroll)
  if kcycle > 0.5 then
    apr phasor acps / kn
    aang = aang + 2 * $M_PI * apr
  endif
  aX = aP * cos(aang)
  aY = aP * sin(aang + kskew * $M_PI * 0.5)
  xout aX, aY
endop

giDivs ftgen 900, 0, 16, -2, 16, 8, 4, 2, 1, 0.6666667, 0.5, 0.3333333, 0.25, 0.1666667, 0.125

opcode KXModeName, S, k
  km xin
  kmi = round(km * 2) / 2
  if kmi < 0.25 then
    Sn strcpyk "LP"
  elseif kmi < 0.75 then
    Sn strcpyk "LP>BP"
  elseif kmi < 1.25 then
    Sn strcpyk "BP"
  elseif kmi < 1.75 then
    Sn strcpyk "BP>HP"
  elseif kmi < 2.25 then
    Sn strcpyk "HP"
  elseif kmi < 2.75 then
    Sn strcpyk "HP>NOTCH"
  elseif kmi < 3.25 then
    Sn strcpyk "NOTCH"
  elseif kmi < 3.75 then
    Sn strcpyk "NOTCH>COMB"
  else
    Sn strcpyk "ALLPASS/COMB"
  endif
  xout Sn
endop

; ---------------------------------------------------------------------
;  Bionic-Lester-style filter: gain/overdrive VCA -> 2-pole state variable
;  with morphing mode 0 LP .. 1 BP .. 2 HP .. 3 notch .. 4 allpass/comb
; ---------------------------------------------------------------------
opcode KXLester, a, akkkk
  ain, kcf, kres, kmode, kgain xin
  kg limit kgain, 0, 1
  if kg <= 0.5 then
    ax = ain * kg * 2
  else
    kd = (kg - 0.5) * 2
    asoft = tanh(ain * (1 + kd * 5))
    ahard limit ain * (1 + kd * 10), -0.8, 0.8
    kh = kd * kd * kd
    ax = asoft * (1 - kh) + ahard * 1.25 * kh
  endif
  krz limit kres, 0, 1
  kq = 0.6 + krz * krz * 11
  kc limit kcf, 20, sr * 0.42
  alp, ahp, abq zdf_2pole_mode ax, kc, kq
  abp = abq / kq
  abr = alp + ahp
  km limit kmode, 0, 4
  kseg = min(int(km), 3)
  kf = km - kseg
  if kseg == 0 then
    aout = alp * (1 - kf) + abp * kf
  elseif kseg == 1 then
    aout = abp * (1 - kf) + ahp * kf
  elseif kseg == 2 then
    aout = ahp * (1 - kf) + abr * kf
  else
    ; allpass / comb: resonance 0 -> allpass, to noon -> +comb, past noon -> -comb
    kfb = (krz < 0.5 ? krz * 2 : -(krz - 0.5) * 2) * 0.96
    adl = a(1 / kc)
    acomb flanger ax, adl, kfb, 0.06
    acomb = acomb * (1 - abs(kfb) * 0.6)
    aout = abr * (1 - kf) + acomb * kf
  endif
  xout aout / (1 + krz * 1.2 + krz * krz * 2.5)
endop

; ---------------------------------------------------------------------
;  Odessa-style additive voice stack (recursive over unison/chord voices)
; ---------------------------------------------------------------------
opcode KXOde, aa, kkiiiiiiiik
  kcps, kspread, iFA, iAA, iFB, iAB, icnt, inum, idx, ichord, ksplit xin
  idet[] fillarray 0, -1, 1, -2, 2
  isemi tab_i ichord * 5 + idx, giChords
  kf = kcps * semitone(isemi + kspread * idet[idx] * 0.35)
  iph random 0, 1
  aA adsynt2 1, kf, giSine, iFA, iAA, icnt
  if ksplit > 0.5 then
    aB adsynt2 1, kf, giSine, iFB, iAB, icnt
  else
    aB = aA
  endif
  aA2 = 0
  aB2 = 0
  if idx < inum - 1 then
    aA2, aB2 KXOde kcps, kspread, iFA, iAA, iFB, iAB, icnt, inum, idx + 1, ichord, ksplit
  endif
  xout aA + aA2, aB + aB2
endop

; ---------------------------------------------------------------------
;  Unison oscillator stack (recursive): returns a stereo pair
; ---------------------------------------------------------------------
opcode KXUni, aa, kkkkkiii
  kcps, kpw, kdet, kspread, kdrift, iwave, inum, iidx xin
  ipos = (inum > 1 ? (iidx / (inum - 1)) * 2 - 1 : 0)
  kdr randomi -1, 1, 0.25 + iidx * 0.11
  kf = kcps * semitone(kdet * ipos * 0.6 + kdr * kdrift * 0.18)
  kf limit kf, 1, sr * 0.45
  kpwc limit kpw, 0.02, 0.98
  iphs random 0, 1
  iphs = (i(gkUniLock) > 0.5 ? 0 : iphs)
  ; knob positions (icons): 1 triangle  2 square/pulse  3 saw  4 sine
  if iwave == 4 then
    a1 poscil 1, kf, giSine, iphs
  elseif iwave == 3 then
    a1 vco2 0.8, kf, 0, 0.5, iphs
  elseif iwave == 2 then
    a1 vco2 0.8, kf, 2, kpwc, iphs
  else
    a1 vco2 0.9, kf, 4, kpwc, iphs
  endif
  kpan = 0.5 + ipos * kspread * 0.5
  kpan limit kpan, 0, 1
  aL = a1 * sqrt(1 - kpan)
  aR = a1 * sqrt(kpan)
  aL2 = 0
  aR2 = 0
  if iidx < inum - 1 then
    aL2, aR2 KXUni kcps, kpw, kdet, kspread, kdrift, iwave, inum, iidx + 1
  endif
  xout aL + aL2, aR + aR2
endop

; ---------------------------------------------------------------------
;  instr 1 : MIDI dispatcher - one per key. Starts a voice (instr 11.slot)
;  and releases it on note-off, unless VCA INIT is holding the chord.
; ---------------------------------------------------------------------
instr 1
  inote notnum
  ivel veloc 0, 127
  islot = i(gkSlot)
  gkSlot init (islot + 1) % 64
  if i(gkHeld) <= 0 then
    gkGen init i(gkGen) + 1
  endif
  gkHeld init i(gkHeld) + 1
  idrone = (i(gkInit) > 0.001 ? 1 : 0)
  ifrac = 11 + (islot + 1) / 1000
  gkNoteN init i(gkNoteN) + 1
  event_i "i", ifrac, 0, -1, inote, ivel, islot, i(gkGen), idrone, i(gkNoteN)
  xtratim 0.05
  gkBend pchbend 0, 2
  gkMWheel midictrl 1, 0, 1
  gkATouch aftouch 0, 1
  krel release
  gkKeyUp[islot] = krel
  kprel init 0                       ; explicit state: 'trigger' keeps its memory when an instance is reused
  koff = 0
  if krel > 0.5 && kprel < 0.5 then
    koff = 1
  endif
  kprel = krel
  if koff == 1 then
    gkHeld = max(gkHeld - 1, 0)
    if idrone == 0 then
      turnoff2 ifrac, 4, 1
    endif
  endif
endin

; ---------------------------------------------------------------------
;  instr 11 : polyphonic voice (one instance per key, p4 note p5 vel
;  p6 slot p7 chord generation p8 drone)
; ---------------------------------------------------------------------
instr 11
  inote = p4
  ivel = p5 / 127
  islot = p6
  igen = p7
  idrone = p8
  iord = p9
  irand random -1, 1
  istart = i(gkLastPitch)
  gkLastPitch init inote

  ; ---- per-note settings
  iwave = round(i(gkWave))
  inum  = round(i(gkUni))
  inum  limit inum, 1, 7

  ; ---- envelopes (original ADSRs)
  iaa = max(i(gkAA), 0.002)
  iad = max(i(gkAD), 0.005)
  ias = i(gkAS)
  iar = max(i(gkAR), 0.01)
  aenvm madsr iaa, iad, ias, iar
  kaenv madsr iaa, iad, ias, iar
  ifa = max(i(gkFA), 0.002)
  ifd = max(i(gkFD), 0.005)
  ifs = i(gkFS)
  ifr = max(i(gkFR), 0.01)
  kfenv madsr ifa, ifd, ifs, ifr
  ; key state: held while the dispatcher's key is down
  kup = gkKeyUp[islot]
  krel release
  kup = (krel == 1 ? 1 : kup)
  ; VCA INIT (polyphonic): after the key goes up, the voice falls to the VCA
  ; INIT level and the whole last chord keeps droning until a new chord starts
  if idrone == 1 then
    krelt init 0
    kalast init 0
    kflast init 0
    if kup == 0 then
      kalast = kaenv
      kflast = kfenv
    else
      krelt += ksmps / sr
      kaenv = kalast * max(0, 1 - krelt / iar)
      kfenv = kflast
    endif
    aenvm interp kaenv
    kalive = 0
    if gkGen == igen && gkNoteN - iord < 8 then        ; the last chord drones, at most 8 notes of it
      kalive = 1
    endif
    kalive portk kalive, 0.08
    aflo interp gkInit * kalive
    aenv max aenvm, aflo
    kdone init 0
    if kup == 1 && kalive < 0.001 && kaenv < 0.0005 && kdone == 0 then
      kdone = 1
      turnoff
    endif
  else
    aenv = aenvm
  endif
  kmenv linseg 0, i(gkMeA), 1, i(gkMeD), 0

  ; ---- voice management: at most 16 voices sound. The oldest is stolen with a 15 ms fade,
  ;      then it idles (no DSP) until Csound lets it go.
  kstolen init 0
  kstf init 1
  if gkNoteN - iord >= 16 && kstolen == 0 then
    kstolen = 1
    turnoff
  endif
  if kstolen == 1 then
    kstf = max(kstf - ksmps / (sr * 0.015), 0)
    if kstf <= 0 kgoto VOICE_END
  endif

  ; ---- MIDI controllers
  kbend = gkBend * gkBendR * 0.5
  kwheel = gkMWheel
  kat = gkATouch

  ; ---- modulation matrix
  kS[] init @NSRC@
  kD[] init @NDST@
  kmdc init 0
  if kmdc == 0 then
    kS[0] = 0
    kS[1] = gkL1
    kS[2] = gkL2
    kS[3] = kmenv
    kS[4] = kaenv
    kS[5] = ivel
    kS[6] = (inote - 60) / 24
    kS[7] = kwheel
    kS[8] = kat
    kS[9] = irand
    kS[10] = gkChaos
    kS[11] = gkNatEnv
    kS[12] = gkFollow
    kS[13] = gkOutEnv
    ibd = islot % 8
    kS[14] = gkBoidX[ibd] * gkScBV
    kS[15] = gkBoidY[ibd] * gkScBV
    kS[16] = gkLorX
    kS[17] = gkLorY
    kS[18] = gkLorZ
    kS[19] = gkCC[0]
    kS[20] = gkCC[1]
    kS[21] = gkCC[2]
    kS[22] = gkCC[3]
    ki = 0
    while ki < @NDST@ do
      kD[ki] = 0
      ki += 1
    od
    ki = 0
    while ki < gkPinN do
      ksrc = int(gkPinS[ki]) - 1
      kdst = int(gkPinD[ki]) - 1
      if ksrc > 0 && kdst > 0 && ksrc < @NSRC@ && kdst < @NDST@ then
        kD[kdst] = kD[kdst] + gkPinA[ki] * kS[ksrc]
      endif
      ki += 1
    od
  endif
  kmdc = (kmdc + 1) % 2
  ; kD index: 1 pitch 2 cutoff 3 res 4 pw 5 fold 6 fm 7 sub 8 noise 9 resonate
  ;           10 detune 11 amp 12 pan 13/14 lfo rates (global) 15 delay 16 reverb
  ;           17 order 18 teeth 19 roll 20 OP amt 21 poly level 22 poly fold
  ;           23 ode partials 24 tilt 25 tension 26 density 27 warp 28 peaking 29 ode level
  ;           30 field pos 31 field size 32 field level 33 B cutoff 34 lester mode 35 lester mix

  ; ---- pitch
  ihalf = i(gkGlide) * 0.4
  kglide portk inote, ihalf, istart
  kpitch = gkL2 * gkVib + kmenv * gkPEnv * 24 + kglide + gkVCO + gkOct + 12 * log2(max(gkTune, 0.01)) + kD[1] * 12 + kbend
  kcps = cpsmidinn(kpitch)
  kcps limit kcps, 4, sr * 0.45

  ; ---- oscillators
  kpw = gkPW + kD[4] * 0.45
  kdet = gkDetune + kD[10]
  kdet limit kdet, 0, 2
  aL, aR KXUni kcps, kpw, kdet, gkSpread, gkDrift, iwave, inum, 0
  igain = 1 / sqrt(inum)
  kvco = gkAmpVCO * 0.5
  aL *= igain * kvco
  aR *= igain * kvco
  amain = (aL + aR) * 0.5

  ; ---- POLYGON oscillator: six "jacks" (source x attenuverter) + matrix
  kJ[] init 6
  ki = 0
  while ki < 6 do
    kjs = int(gkJS[ki]) - 1
    if kjs > 0 && kjs < @NSRC@ then
      kJ[ki] = gkJA[ki] * kS[kjs]
    else
      kJ[ki] = 0
    endif
    ki += 1
  od
  kpl limit gkPLevel + kD[21], 0, 1
  if kpl > 0.001 then
    kpo = gkPOrder + kJ[1] * 5 + kD[17] * 5
    if gkPRegular > 0.5 then
      kpo = round(kpo)
    endif
    kpo limit kpo, 2.05, 32
    kpt limit gkPTeeth + kJ[2] + kD[18], 0, 1
    kpo portk kpo, gkPSlew
    kpt portk kpt, gkPSlew
    kspn init 0
    kspn += gkPSpin * ksmps / sr
    kpr = gkPRoll + kJ[3] + kD[19] + kspn
    kpq = gkPRatio * 2 ^ (kJ[4] * 2)
    if gkPSnap > 0.5 then
      kpq = (kpq < 0.75 ? 0.5 : round(kpq))
    endif
    kpa limit gkPAmt + kJ[5] + kD[20], 0, 1
    kpc = cpsmidinn(kpitch + gkPTune + kJ[0] * 24)
    kpc limit kpc, 2, sr * 0.4
    apc = kpc * (1 + gkPFM * amain * 3)
    aPX, aPY KXPoly apc, kpo, kpt, kpr, kpq, kpa, gkPCycle, gkPSkew
    kpf limit gkPFold + kD[22], 0, 1
    if kpf > 0.001 then
      kfg2 = 1 + kpf * 6
      aPX = aPX * (1 - kpf) + sin(aPX * kfg2) * kpf
      aPY = aPY * (1 - kpf) + sin(aPY * kfg2) * kpf
    endif
    gaDispX += aPX
    gaDispY += aPY
    kwd = gkPWidth
    aPL = aPX * (1 + kwd) * 0.5 + aPY * (1 - kwd) * 0.5
    aPR = aPY * (1 + kwd) * 0.5 + aPX * (1 - kwd) * 0.5
    aL += aPL * kpl * 0.9
    aR += aPR * kpl * 0.9
  endif


  ; ---- ODESSA additive layer (built only if its level is up at note-on)
  if i(gkOLevel) > 0.0005 then
    ipart = i(gkOPart)
    iFA ftgentmp 0, 0, 128, -2, 0
    iAA ftgentmp 0, 0, 128, -2, 0
    iFB ftgentmp 0, 0, 128, -2, 0
    iAB ftgentmp 0, 0, 128, -2, 0
    iov = round(i(gkOVoices))
    inv = 1
    if iov >= 5 then
      inv = 5
    elseif iov >= 3 then
      inv = 3
    endif
    icnt = min((inv == 5 ? 64 : 128), 2 ^ ceil(log2(max(8, ipart))))
    ichord = limit(round(i(gkOChord)) - 1, 0, 11)
    imax = 0
    ij = 0
    while ij < inv do
      imax = max(imax, tab_i(ichord * 5 + ij, giChords))
      ij += 1
    od
    imaxr = semitone(imax + 1)
    ; four "CV sliders": 0 exp FM, 1 lin FM, 2 density, 3 warp
    kOC[] init 4
    kj = 0
    while kj < 4 do
      kos = int(gkOCvS[kj]) - 1
      if kos > 0 && kos < @NSRC@ then
        kOC[kj] = gkOCvA[kj] * kS[kos]
      else
        kOC[kj] = 0
      endif
      kj += 1
    od
    koc = kcps * semitone(gkOTune + gkOFine / 100 + kOC[0] * 24)
    koc = koc * abs(1 + kOC[1] * 2)
    koc limit koc, 1, sr * 0.45
    kocnt init 0
    kocnt += 1
    if kocnt % 4 == 1 then
      kopart limit gkOPart + kD[23] * 64, 1, icnt
      kotilt limit gkOTilt + kD[24], 0, 1
      kogam = 3 * (1 - kotilt) ^ 1.585
      koten limit gkOTension + kD[25], -1, 1
      if koten > 0.04 then
        koten = (koten - 0.04) / 0.96
      elseif koten < -0.04 then
        koten = (koten + 0.04) / 0.96
      else
        koten = 0
      endif
      koden limit gkODens + kOC[2] + kD[26], 0, 1
      kowarp limit gkOWarp + kOC[3] + kD[27], 0, 1
      kopk limit gkOPeak + kD[28], 0, 1
      koqx = 0.15 * 30 ^ kopk
      koP = (koden > 0.001 ? 2 / koden : 0)
      koa = 1 / (1 + 3 * kowarp)
      koc512 = 512 ^ (1 - koa)
      kobank = round(gkOBank)
      koL = abs(kobank)
      koLg = max(1, koL)
      kofi = round(gkOFactor)
      kofac = (kofi >= 0 ? kofi + 1 : 1 / (1 - kofi))
      konyq = sr * 0.45 / (koc * imaxr)
      kosum = 0
      kon = 1
      while kon <= icnt do
        kor = 1
        if kon > 1 then
          kor = abs(1 + (kon - 1) * (1 + koten * 0.06 * (kon - 1)))
          kor = max(kor, 0.05)
        endif
        kocomb = 1
        if koP > 0 then
          koar = $M_PI * koc512 * kor ^ koa / koP
          kocomb = abs(sin(koar) / koar) ^ koqx
        endif
        koamp = kon ^ (-kogam) * kocomb
        if kon > kopart then
          koamp = koamp * max(0, 1 - (kon - kopart))
        endif
        koinA = 1
        koinB = 1
        korA = kor
        korB = kor
        if kon >= 2 then
          kogi = min(7, int((kon - 2) / koLg))
          if gkOG[kogi] < 0.5 then
            koamp = 0
          endif
          if koL > 0 then
            kopar = int((kon - 2) / koL) % 2
            koinA = kopar
            koinB = 1 - kopar
          endif
          if kobank >= 0 then
            korB = kor * kofac
          else
            korA = kor * kofac
          endif
        endif
        koaA = (korA < konyq ? koamp * koinA : 0)
        koaB = (korB < konyq ? koamp * koinB : 0)
        tablew korA, kon - 1, iFA
        tablew koaA, kon - 1, iAA
        tablew korB, kon - 1, iFB
        tablew koaB, kon - 1, iAB
        kosum += koaA * koaA + (koL > 0 ? koaB * koaB : 0)
        kon += 1
      od
      konorm = 1 / sqrt(max(kosum, 0.000001))
    endif
    kosplit = (koL > 0 ? 1 : 0)
    aOA, aOB KXOde koc, gkOSpread, iFA, iAA, iFB, iAB, icnt, inv, 0, ichord, kosplit
    konm portk konorm, 0.01
    aOA *= konm * 0.75 / sqrt(inv)
    aOB *= konm * 0.75 / sqrt(inv)
    kofu = gkOFund
    if kofu > 0.001 then
      if gkOFundSq > 0.5 then
        afu vco2 0.6, koc, 10
      else
        afu poscil 0.8, koc
      endif
      aOA += afu * kofu
      aOB += afu * kofu
    endif
    kow = gkOWidth
    aOL = aOA * (1 + kow) * 0.5 + aOB * (1 - kow) * 0.5
    aOR = aOB * (1 + kow) * 0.5 + aOA * (1 - kow) * 0.5
    kolv limit gkOLevel + kD[29], 0, 1
    aL += aOL * kolv
    aR += aOR * kolv
  endif

  ; ---- FIELD layer: the stock recordings, micro-looped and played from the keys
  if i(gkFVoice) > 0.0005 && i(gkFTabL) > 0 then
    iftl = i(gkFTabL)
    iftr = i(gkFTabR)
    ifln = i(gkFLen)
    iscat random -1, 1
    kfpos limit gkFPos + kD[30] + iscat * gkFScatter * 0.5 + (gkLpA - 0.5) * 0.24, 0, 0.97
    kfsz limit (gkFSize + kD[31]) * (0.6 + gkLpB * 0.8), 0.003, 1
    kfst = kfpos * ifln
    kfen = min(ifln, kfst + kfsz * ifln)
    kfxf = min(0.05, (kfen - kfst) * 0.3)
    kfp = semitone(gkFPitch) * gkFSrFix
    if gkFKey > 0.5 then
      kfp = kfp * semitone(kpitch - 60 - gkOct - gkVCO)
    endif
    ifst = limit(i(gkFPos) + iscat * i(gkFScatter) * 0.5, 0, 0.97) * ifln
    afl flooper2 1, kfp, kfst, kfen, kfxf, iftl, ifst
    afr flooper2 1, kfp, kfst, kfen, kfxf, iftr, ifst
    gaFieldRaw += (afl + afr) * 0.5
    kflv limit gkFVoice + kD[32], 0, 1
    kflv = kflv * kflv * 1.1 * gkFNorm
    aL += afl * kflv
    aR += afr * kflv
  endif

  ; sub oscillator (square, one octave down)
  ksub limit gkSub + kD[7], 0, 1
  if ksub > 0.001 then
    asub vco2 0.7, kcps * (gkSub2 > 0.5 ? 0.25 : 0.5), 10
    aL += asub * ksub
    aR += asub * ksub
  endif

  ; FM layer: sine carrier/modulator pair, index swept by the FM amount
  kfm limit gkFM + kD[6], 0, 1
  if kfm > 0.001 then
    afm foscili 0.8, kcps, 1, gkFMRatio, kfm * 9, giSine
    kfml = min(1, kfm * 2.5)
    aL += afm * kfml
    aR += afm * kfml
  endif

  ; wavefolder
  kfold limit gkFold + kD[5], 0, 1
  if kfold > 0.001 then
    kfg = 1 + kfold * 7
    aL = aL * (1 - kfold) + sin(aL * kfg) * kfold
    aR = aR * (1 - kfold) + sin(aR * kfg) * kfold
  endif

  ; noise (Tone = noise colour, as on the hardware mixer)
  knz limit gkNoise + kD[8] * 0.5, 0, 1
  if knz > 0.0005 then
    anz noise 1, 0
    ktn limit gkTone, 1, 12000
    anz butlp anz, ktn
    anz butlp anz, ktn
    aL += anz * knz * 1.6
    aR += anz * knz * 1.6
  endif

  ; nature resonator: the selected nature sound rings at the note's pitch
  kres_n limit gkResonate + kD[9], 0, 1
  if kres_n > 0.001 then
    astr wguide1 gaNatPrev * 6, kcps, 9000, 0.985
    astr dcblock2 astr
    aL += astr * kres_n * 0.5
    aR += astr * kres_n * 0.5
  endif

  ; ---- FILTER: Bionic-Lester-style dual morphing filter
  ;      A = the top-panel Cutoff / Resonance / Mod (env); B = the Lester page
  kLa[] init 4
  kLb[] init 4
  kj = 0
  while kj < 4 do
    kLa[kj] = 0
    kLb[kj] = 0
    kj += 1
  od
  kj = 0
  while kj < 6 do
    kls = int(gkLCvS[kj]) - 1
    if kls > 0 && kls < @NSRC@ then
      kldv = gkLCvA[kj] * kS[kls]
      kldd limit int(gkLCvD[kj]) - 1, 0, 3
      if kj < 3 then
        kLa[kldd] = kLa[kldd] + kldv
      else
        kLb[kldd] = kLb[kldd] + kldv
      endif
    endif
    kj += 1
  od
  koctA = log2(gkLP) - gkMod * (1 - kfenv) * 6 + kD[2] * 5 + kLa[0] * 5
  kcfA limit 2 ^ koctA, 25, min(18000, sr * 0.42)
  kcfA portk kcfA, 0.004
  kqA limit gkRes + kD[3] * 0.5 + kLa[1], 0, 1
  kmA limit gkAMode + kD[34] * 4 + kLa[2] * 4, 0, 4
  kgA limit gkAGain + kLa[3] * 0.5 + kD[36] * 0.5, 0, 1
  klink = round(gkLink)
  if klink == 4 || klink == 5 then
    kcfB = kcfA
    kqB = kqA
    kmB = kmA
    kgB = kgA
  else
    koctB = log2(gkBCut) + kD[33] * 5 + kLb[0] * 5
    if klink == 2 then
      koctB = koctA + log2(gkBCut) - 9.3 + kD[33] * 5 + kLb[0] * 5
    endif
    kcfB limit 2 ^ koctB, 25, min(18000, sr * 0.42)
    kcfB portk kcfB, 0.004
    kqB limit gkBRes + kLb[1], 0, 1
    kmB limit gkBMode + kD[34] * 4 + kLb[2] * 4, 0, 4
    kgB limit gkBGain + kLb[3] * 0.5 + kD[36] * 0.5, 0, 1
  endif
  kmix limit gkLMix + kD[35], 0, 1
  if klink == 5 then
    aL KXLester aL, kcfA, kqA, kmA, kgA
    aR KXLester aR, kcfB, kqB, kmB, kgB
  elseif klink == 3 || klink == 4 then
    aAL KXLester aL, kcfA, kqA, kmA, kgA
    aAR KXLester aR, kcfA, kqA, kmA, kgA
    aBL KXLester aAL, kcfB, kqB, kmB, kgB
    aBR KXLester aAR, kcfB, kqB, kmB, kgB
    aL = aAL * (1 - kmix) + aBL * kmix
    aR = aAR * (1 - kmix) + aBR * kmix
  else
    aAL KXLester aL, kcfA, kqA, kmA, kgA
    aAR KXLester aR, kcfA, kqA, kmA, kgA
    aBL KXLester aL, kcfB, kqB, kmB, kgB
    aBR KXLester aR, kcfB, kqB, kmB, kgB
    aL = aAL * (1 - kmix) + aBL * kmix
    aR = aAR * (1 - kmix) + aBR * kmix
  endif

  ; ---- VCA
  kvel = 1 - gkVelAmt + gkVelAmt * ivel
  kamp limit (1 + kD[11]) * kvel, 0, 2
  kamp portk kamp, 0.004
  aL *= aenv * kamp * 0.26 * kstf
  aR *= aenv * kamp * 0.26 * kstf
  ; DRIVE saturates each voice on its own, so chords stay clean (no intermodulation of the whole mix)
  kvdg = 1 + gkDrive * 7
  kvdc = 1 / (1 + gkDrive * 2.5)
  aL = tanh(aL * kvdg) * kvdc
  aR = tanh(aR * kvdg) * kvdc

  ipanr random -1, 1
#ifdef SONIC
  ; ---- this voice is a point in space: it rides bird (slot mod 12), and the
  ;      matrix's space destinations push it further, round, up, wider, astray
  ib = islot % 12
  isx random -1, 1
  isy random -1, 1
  isz random -1, 1
  kdsc = 2 ^ limit(kD[37] * 2, -3, 3)
  kaz = kD[38] * 3.14159 + kD[12] * 1.5708 + ipanr * gkVStereo * 0.8
  kaz portk kaz, 0.02
  kpx = gkPX[ib]
  kpy = gkPY[ib]
  kxr = (kpx * cos(kaz) - kpy * sin(kaz)) * kdsc
  kyr = (kpx * sin(kaz) + kpy * cos(kaz)) * kdsc
  kzr = gkPZ[ib] * kdsc + kD[39] * gkSpDist
  kdv = kD[41] * gkSpDist * 0.6
  kxr = kxr + isx * kdv
  kyr = kyr + isy * kdv
  kzr = kzr + isz * kdv * 0.6
  amono = (aL + aR) * 0.7071
  SpPoint amono, kxr, kyr, kzr, gkSpSpread + kD[40], gkSpAir + kD[42]
#else
  kpan limit 0.5 + kD[12] * 0.5 + ipanr * gkVStereo * 0.5, 0, 1
  kpan portk kpan, 0.01
  aL *= sqrt(1 - kpan) * 1.414
  aR *= sqrt(kpan) * 1.414

  gaVL += aL
  gaVR += aR
#end
  kds limit 1 + kD[15], 0, 2
  krs limit 1 + kD[16], 0, 2
  gaDlyL += aL * kds
  gaDlyR += aR * kds
  gaRevL += aL * krs
  gaRevR += aR * krs
VOICE_END:
endin

; ---------------------------------------------------------------------
;  instr 2 : controls, global LFOs, chaos, GUI feedback
; ---------------------------------------------------------------------
instr 2
  gkVCO chnget "VCO"
  gkTune chnget "Tune1"
  kDn chnget "OctDn"
  k0 chnget "Oct0"
  kUp chnget "OctUp"
  if kUp > 0.5 then
    gkOct = 0
  elseif k0 > 0.5 then
    gkOct = -12
  else
    gkOct = -24
  endif
  gkWave chnget "waveform"
  gkPW chnget "pw"
  gkLP chnget "LPFreq"
  gkLP limit gkLP, 20, 20000
  gkRes chnget "Res"
  gkMod chnget "mod"
  gkFA chnget "FAtt"
  gkFD chnget "FDec"
  gkFS chnget "FSus"
  gkFR chnget "FRel"
  gkAA chnget "AAtt"
  gkAD chnget "ADec"
  gkAS chnget "ASus"
  gkAR chnget "ARel"
  gkInit chnget "VCAinit"
  gkTone chnget "tone"
  gkVol chnget "volume"
  gkAmpVCO chnget "ampVCO"
  gkNoise chnget "noise"
  gkRev chnget "reverb"
  gkSamp chnget "AmpSamp"
@SREAD@

  gkMeA chnget "meAtt"
  gkMeD chnget "meDec"
  gkUni chnget "uni"
  gkDetune chnget "detune"
  gkSpread chnget "spread"
  gkDrift chnget "drift"
  gkSub chnget "sub"
  gkFM chnget "fm"
  gkFMRatio chnget "fmRatio"
  gkFold chnget "fold"
  gkGlide chnget "glide"
  gkResonate chnget "resonate"
  gkVelAmt chnget "velAmt"
  gkChorus chnget "chorus"
  gkDrive chnget "drive"
  gkDlyMix chnget "dlyMix"
  gkDlyTime chnget "dlyTime"
  gkDlyFb chnget "dlyFb"
  gkSpace chnget "space"

  gkMS[0] chnget "src1"
  gkMS[1] chnget "src2"
  gkMS[2] chnget "src3"
  gkMS[3] chnget "src4"
  gkMS[4] chnget "src5"
  gkMS[5] chnget "src6"
  gkMS[6] chnget "src7"
  gkMS[7] chnget "src8"
  gkMD[0] chnget "dst1"
  gkMD[1] chnget "dst2"
  gkMD[2] chnget "dst3"
  gkMD[3] chnget "dst4"
  gkMD[4] chnget "dst5"
  gkMD[5] chnget "dst6"
  gkMD[6] chnget "dst7"
  gkMD[7] chnget "dst8"
  gkMA[0] chnget "amt1"
  gkMA[1] chnget "amt2"
  gkMA[2] chnget "amt3"
  gkMA[3] chnget "amt4"
  gkMA[4] chnget "amt5"
  gkMA[5] chnget "amt6"
  gkMA[6] chnget "amt7"
  gkMA[7] chnget "amt8"

  gkPTune chnget "pTune"
  gkPOrder chnget "pOrder"
  gkPTeeth chnget "pTeeth"
  gkPRoll chnget "pRoll"
  gkPRatio chnget "pRatio"
  gkPAmt chnget "pAmt"
  gkPFM chnget "pFM"
  gkPFold chnget "pFold"
  gkPLevel chnget "pLevel"
  gkPWidth chnget "pWidth"
  gkPSlew chnget "pSlew"
  gkPSpin chnget "pSpin"
  gkPSkew chnget "pPhase"
  gkPCycle chnget "pCycle"
  gkPRegular chnget "pRegular"
  gkPSnap chnget "pSnap"
  gkJS[0] chnget "j1Src"
  gkJS[1] chnget "j2Src"
  gkJS[2] chnget "j3Src"
  gkJS[3] chnget "j4Src"
  gkJS[4] chnget "j5Src"
  gkJS[5] chnget "j6Src"
  gkJA[0] chnget "j1Att"
  gkJA[1] chnget "j2Att"
  gkJA[2] chnget "j3Att"
  gkJA[3] chnget "j4Att"
  gkJA[4] chnget "j5Att"
  gkJA[5] chnget "j6Att"

  ; free-running preview of the polygon for the XY screen (shown when idle)
  kvo = gkPOrder
  if gkPRegular > 0.5 then
    kvo = round(kvo)
  endif
  kvq = gkPRatio
  if gkPSnap > 0.5 then
    kvq = (kvq < 0.75 ? 0.5 : round(kvq))
  endif
  kvs init 0
  kvs += gkPSpin * ksmps / sr
  gaPrevX, gaPrevY KXPoly a(97.999), kvo, gkPTeeth, gkPRoll + kvs, kvq, gkPAmt, gkPCycle, gkPSkew

  ; ---- odessa
  gkOTune chnget "oTune"
  gkOFine chnget "oFine"
  gkOSpread chnget "oSpread"
  kovs chnget "oVoices"
  gkOVoices = round(kovs) * 2 - 1
  gkOChord chnget "oChord"
  gkOPart chnget "oPart"
  gkOTension chnget "oTension"
  gkOTilt chnget "oTilt"
  gkOBank chnget "oBank"
  gkOFactor chnget "oFactor"
  gkODens chnget "oDens"
  gkOWarp chnget "oWarp"
  gkOPeak chnget "oPeak"
  gkOFund chnget "oFund"
  kofw chnget "oFundWave"
  gkOFundSq = (kofw > 1.5 ? 1 : 0)
  gkOLevel chnget "oLevel"
  gkOWidth chnget "oWidth"
  gkOG[0] chnget "oG1"
  gkOG[1] chnget "oG2"
  gkOG[2] chnget "oG3"
  gkOG[3] chnget "oG4"
  gkOG[4] chnget "oG5"
  gkOG[5] chnget "oG6"
  gkOG[6] chnget "oG7"
  gkOG[7] chnget "oG8"
  gkOCvS[0] chnget "oExpSrc"
  gkOCvS[1] chnget "oLinSrc"
  gkOCvS[2] chnget "oDenSrc"
  gkOCvS[3] chnget "oWarpSrc"
  gkOCvA[0] chnget "oExpAtt"
  gkOCvA[1] chnget "oLinAtt"
  gkOCvA[2] chnget "oDenAtt"
  gkOCvA[3] chnget "oWarpAtt"
  ; ---- field
  gkFSpeed chnget "fSpeed"
  gkFRev chnget "fRev"
  gkFVoice chnget "fVoice"
  gkFPitch chnget "fPitch"
  gkFKey chnget "fKey"
  gkFPos chnget "fPos"
@CCREAD@
#ifdef SONIC
  gkSpMode chnget "spMode"
  gkSpSpeed chnget "spSpeed"
  gkSpDist chnget "spDist"
  gkSpHeight chnget "spHeight"
  gkSpDev chnget "spDev"
  gkSpRot chnget "spRot"
  gkSpSpread chnget "spSpread"
  gkSpDopp chnget "spDopp"
  gkSpAir chnget "spAir"
  gkSpGrav chnget "spGrav"
  gkSpCoh chnget "spCoh"
  gkSpFSplay chnget "spFSplay"
#end
  ; field recording loop points slew slowly, at the pace of the drifting topography
  gkLpA rspline 0, 1, 0.15 / (@NIDLE@ * giIdleStep), 1 / (@NIDLE@ * giIdleStep)
  gkLpB rspline 0, 1, 0.15 / (@NIDLE@ * giIdleStep), 1 / (@NIDLE@ * giIdleStep)
  gkFSize chnget "fSize"
  gkFScatter chnget "fScatter"
  gkFAtt chnget "fAtt"
  gkFRel chnget "fRel"
  gkFGain chnget "fGain"
  ; ---- lester
  gkAMode chnget "aMode"
  gkAGain chnget "aGain"
  gkBCut chnget "bCut"
  gkBRes chnget "bRes"
  gkBMode chnget "bMode"
  gkBGain chnget "bGain"
  gkLink chnget "link"
  gkLMix chnget "lMix"
  gkLCvS[0] chnget "a1Src"
  gkLCvS[1] chnget "a2Src"
  gkLCvS[2] chnget "a3Src"
  gkLCvS[3] chnget "b1Src"
  gkLCvS[4] chnget "b2Src"
  gkLCvS[5] chnget "b3Src"
  gkLCvA[0] chnget "a1Att"
  gkLCvA[1] chnget "a2Att"
  gkLCvA[2] chnget "a3Att"
  gkLCvA[3] chnget "b1Att"
  gkLCvA[4] chnget "b2Att"
  gkLCvA[5] chnget "b3Att"
  gkLCvD[0] = 1
  gkLCvD[1] chnget "a2Dst"
  gkLCvD[2] chnget "a3Dst"
  gkLCvD[3] = 1
  gkLCvD[4] chnget "b2Dst"
  gkLCvD[5] chnget "b3Dst"

  ; ================= SWARM: boids + lorenz =================
  gkVStereo chnget "vStereo"
  gkPEnv chnget "pEnv"
  gkVib chnget "vib"
  gkBendR chnget "bendRange"
  kbd chnget "bDepth"
  kld chnget "lDepth"
  kbs chnget "bSpeed"
  kbco chnget "bCoh"
  kbse chnget "bSep"
  kbal chnget "bAli"
  klr chnget "lRate"
  kls chnget "lSigma"
  klo chnget "lRho"
  klb chnget "lBeta"
  ksc0 chnget "scSource"
  ksc1 chnget "scPoly"
  ksc2 chnget "scOde"
  ksc3 chnget "scFilt"
  ksc4 chnget "scFx"
  ksc5 chnget "scMot"
  gkScBV chnget "scBoidV"
  gkUniLock chnget "uniLock"
  gkSub2 chnget "sub2"
  gkSwB[0] = kbd * ksc0
  gkSwB[1] = kbd * ksc1
  gkSwB[2] = kbd * ksc2
  gkSwB[3] = kbd * ksc3
  gkSwB[4] = kbd * ksc4
  gkSwB[5] = kbd * ksc5
  gkSwL[0] = kld * ksc0
  gkSwL[1] = kld * ksc1
  gkSwL[2] = kld * ksc2
  gkSwL[3] = kld * ksc3
  gkSwL[4] = kld * ksc4
  gkSwL[5] = kld * ksc5

  ; boids: 8 agents in a [-1,1] box (cohesion, separation, alignment, walls, wander)
  kbinit init 1
  if kbinit == 1 then
    kb = 0
    while kb < 8 do
      gkBoidX[kb] = random:k(-0.8, 0.8)
      gkBoidY[kb] = random:k(-0.8, 0.8)
      gkBVX[kb] = random:k(-0.01, 0.01)
      gkBVY[kb] = random:k(-0.01, 0.01)
      kb += 1
    od
    kbinit = 0
  endif
  kbcnt init 0
  kbcnt += 1
  if kbcnt % 2 == 0 then
    kvmax = 0.0006 + kbs * kbs * 0.02
    kb = 0
    while kb < 8 do
      kcx = 0
      kcy = 0
      kax = 0
      kay = 0
      ksx = 0
      ksy = 0
      kn = 0
      kj = 0
      while kj < 8 do
        if kj != kb then
          kdx = gkBoidX[kj] - gkBoidX[kb]
          kdy = gkBoidY[kj] - gkBoidY[kb]
          kd2 = kdx * kdx + kdy * kdy
          if kd2 < 0.6 then
            kcx += kdx
            kcy += kdy
            kax += gkBVX[kj]
            kay += gkBVY[kj]
            kn += 1
            if kd2 < 0.05 then
              ksx -= kdx / (kd2 + 0.002)
              ksy -= kdy / (kd2 + 0.002)
            endif
          endif
        endif
        kj += 1
      od
      kvx = gkBVX[kb]
      kvy = gkBVY[kb]
      if kn > 0 then
        kvx += kcx / kn * kbco * kvmax * 0.06 + (kax / kn - kvx) * kbal * 0.08
        kvy += kcy / kn * kbco * kvmax * 0.06 + (kay / kn - kvy) * kbal * 0.08
      endif
      kvx += ksx * kbse * kvmax * 0.0015
      kvy += ksy * kbse * kvmax * 0.0015
      kpx = gkBoidX[kb]
      kpy = gkBoidY[kb]
      kvx -= kpx * kpx * kpx * kvmax * 0.25
      kvy -= kpy * kpy * kpy * kvmax * 0.25
      kvx += random:k(-1, 1) * kvmax * 0.08
      kvy += random:k(-1, 1) * kvmax * 0.08
      kv = sqrt(kvx * kvx + kvy * kvy)
      if kv > kvmax then
        kvx *= kvmax / kv
        kvy *= kvmax / kv
      endif
      gkBVX[kb] = kvx
      gkBVY[kb] = kvy
      gkBoidX[kb] = limit(kpx + kvx, -1, 1)
      gkBoidY[kb] = limit(kpy + kvy, -1, 1)
      kb += 1
    od
  endif

  ; lorenz attractor (sigma / rho / beta live), normalised to about -1..1
  klx init 0.1
  kly init 0
  klz init 20
  kldt = (0.05 + klr * klr * 4) * ksmps / sr
  kli = 0
  while kli < 2 do
    kdlx = kls * (kly - klx)
    kdly = klx * (klo - klz) - kly
    kdlz = klx * kly - klb * klz
    klx += kdlx * kldt * 0.5
    kly += kdly * kldt * 0.5
    klz += kdlz * kldt * 0.5
    kli += 1
  od
  if abs(klx) > 1000 || abs(kly) > 1000 || abs(klz) > 1000 then
    klx = 0.1
    kly = 0
    klz = 20
  endif
  gkLorX limit klx / 20, -1, 1
  gkLorY limit kly / 27, -1, 1
  gkLorZ limit (klz - klo + 1) / (klo * 0.8 + 1), -1, 1
  gkChaos = gkLorX

@GMOD@

@PINREAD@
  kbpm chnget "HOST_BPM"
  gkBPM = (kbpm > 20 ? kbpm : 120)
  gkWheel ctrl7 1, 1, 0, 1

  ; ---- global sources -> LFO rate destinations
  kG[] init @NSRC@
  kG[1] = gkL1
  kG[2] = gkL2
  kG[7] = gkWheel
  kG[10] = gkChaos
  kG[11] = gkNatEnv
  kG[12] = gkFollow
  kG[13] = gkOutEnv
  kG[14] = gkBoidX[0]
  kG[15] = gkBoidY[0]
  kG[16] = gkLorX
  kG[17] = gkLorY
  kG[18] = gkLorZ
  kG[19] = gkCC[0]
  kG[20] = gkCC[1]
  kG[21] = gkCC[2]
  kG[22] = gkCC[3]
  kr1 = 0
  kr2 = 0
  ki = 0
  while ki < gkPinN do
    ks = int(gkPinS[ki]) - 1
    kd = int(gkPinD[ki]) - 1
    if ks > 0 && ks < @NSRC@ then
      if kd == 13 then
        kr1 += gkPinA[ki] * kG[ks]
      elseif kd == 14 then
        kr2 += gkPinA[ki] * kG[ks]
      endif
    endif
    ki += 1
  od

  kl1r chnget "l1Rate"
  kl1s chnget "l1Shape"
  kl1y chnget "l1Sync"
  kl2r chnget "l2Rate"
  kl2s chnget "l2Shape"
  kl2y chnget "l2Sync"
  if kl1y > 0.5 then
    kl1r KXSync kl1r, gkBPM
  endif
  if kl2y > 0.5 then
    kl2r KXSync kl2r, gkBPM
  endif
  gkL1 KXLfo kl1r * 2 ^ (kr1 * 3), kl1s
  gkL2 KXLfo kl2r * 2 ^ (kr2 * 3), kl2s


  ; ---- GUI feedback (waveform icons, info box, motion page, LFO LEDs)
  kfirst init 1
  ; re-send GUI state now and then: the editor may open long after a change
  kresend metro 2
  kfirst = kfirst + kresend
  kw changed gkWave
  kw = kw + kfirst
  kwv = round(gkWave)
  cabbageSet kw, "Swave1", "visible", (kwv == 4 ? 1 : 0)
  cabbageSet kw, "Swave2", "visible", (kwv == 3 ? 1 : 0)
  cabbageSet kw, "Swave3", "visible", (kwv == 2 ? 1 : 0)
  cabbageSet kw, "Swave4", "visible", (kwv == 1 ? 1 : 0)
  kinfo chnget "info"
  ki2 changed kinfo
  kled metro 25
  ; ---- tabs: polygon / odessa / field / lester
  kt1 chnget "tPoly"
  kt2 chnget "tOde"
  kt3 chnget "tLest"
  kt4 chnget "tMot"
  kt5 chnget "tMat"
  kt6 chnget "tSwarm"
#ifdef SONIC
  kt7 chnget "tSpace"
#end
  ktab = 1
  if kt2 > 0.5 then
    ktab = 2
  elseif kt3 > 0.5 then
    ktab = 3
  elseif kt4 > 0.5 then
    ktab = 4
  elseif kt5 > 0.5 then
    ktab = 5
  elseif kt6 > 0.5 then
    ktab = 6
  endif
#ifdef SONIC
  if kt7 > 0.5 then
    ktab = 7
  endif
#end
  ; ---- topography morph between pages: old controls go, the landscape flows
  ;      through a shared middle shape (@NFR@ frames each way), new controls arrive
  kcur init 1
  kidl init 0
  kfrom init 1
  kanim init 0
  kfr30 metro 30
  if ktab != kcur && kanim == 0 && kidl == 0 then
    kfrom = kcur
    kcur = ktab
    kanim = 1
    cabbageSet 1, "polypanel", "visible", 0
    cabbageSet 1, "odepanel", "visible", 0
    cabbageSet 1, "lestpanel", "visible", 0
    cabbageSet 1, "motpanel", "visible", 0
    cabbageSet 1, "swarmpanel", "visible", 0
#ifdef SONIC
    cabbageSet 1, "spacepanel", "visible", 0
#end
    cabbageSet 1, "matpanel", "visible", 0
  endif
  if kanim > 0 && kfr30 == 1 then
    if kanim <= @NFR@ then
      Sbg sprintfk "bg_%d_%d.png", kfrom, kanim
    else
      Sbg sprintfk "bg_%d_%d.png", kcur, 2 * @NFR@ - kanim
    endif
    cabbageSet 1, "image6", "file", Sbg
    kanim += 1
    if kanim > 2 * @NFR@ then
      kanim = 0
      kfirst = 1
    endif
  endif
  ; ---- idle drift: the landscape keeps morphing - a loop of @NIDLE@ rendered shapes, one new shape
  ;      every frame at @IDLEFPS@ fps (each frame is a real step of the topography, not a crossfade)
  kidir init 1
  kidt metro @IDLEFPS@
  if kanim > 0 then
    kidl = 0
  elseif kidt == 1 && (kcur != 5 || ktab != kcur || kidl != 0) then      ; the matrix board hides the land: no redraws there
    if ktab != kcur || kcur == 5 then
      ; a page change is waiting: run the land quickly back to its resting shape, then morph
      if kidl < @NIDLE@ / 2 then
        kidl = max(kidl - 6, 0)
      else
        kidl = kidl + 6
        kidl = (kidl >= @NIDLE@ ? 0 : kidl)
      endif
    else
      ; wander back and forth through the loop so the motion never repeats
      if random:k(0, 1) < 0.012 then
        kidir = -kidir
      endif
      kidl = (kidl + kidir * 2 + @NIDLE@) % @NIDLE@        ; two shapes per redraw: same speed, half the drawing
    endif
    if kidl == 0 then
      Sbgi sprintfk "bg_%d_0.png", kcur
    else
      Sbgi sprintfk "bg_%d_i%d.png", kcur, kidl
    endif
    cabbageSet 1, "image6", "file", Sbgi
  endif
  ; show the current page (also re-sent now and then for a freshly opened editor)
  if kfirst == 1 && kanim == 0 then
    cabbageSet 1, "polypanel", "visible", (kcur == 1 ? 1 : 0)
    cabbageSet 1, "odepanel", "visible", (kcur == 2 ? 1 : 0)
    cabbageSet 1, "lestpanel", "visible", (kcur == 3 ? 1 : 0)
    cabbageSet 1, "motpanel", "visible", (kcur == 4 ? 1 : 0)
    cabbageSet 1, "matpanel", "visible", (kcur == 5 ? 1 : 0)
    cabbageSet 1, "swarmpanel", "visible", (kcur == 6 ? 1 : 0)
#ifdef SONIC
    cabbageSet 1, "spacepanel", "visible", (kcur == 7 ? 1 : 0)
#end
  endif
@SPDOTS@
@LZDOTS@
  kbdt metro 24
  if kcur == 6 then
    cabbageSet kbdt, "bd1", "bounds", 254 + (gkBoidX[0] + 1) * 82, 23 + (gkBoidY[0] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd2", "bounds", 254 + (gkBoidX[1] + 1) * 82, 23 + (gkBoidY[1] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd3", "bounds", 254 + (gkBoidX[2] + 1) * 82, 23 + (gkBoidY[2] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd4", "bounds", 254 + (gkBoidX[3] + 1) * 82, 23 + (gkBoidY[3] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd5", "bounds", 254 + (gkBoidX[4] + 1) * 82, 23 + (gkBoidY[4] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd6", "bounds", 254 + (gkBoidX[5] + 1) * 82, 23 + (gkBoidY[5] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd7", "bounds", 254 + (gkBoidX[6] + 1) * 82, 23 + (gkBoidY[6] + 1) * 67, 8, 8
    cabbageSet kbdt, "bd8", "bounds", 254 + (gkBoidX[7] + 1) * 82, 23 + (gkBoidY[7] + 1) * 67, 8, 8
  endif
  gkTab = kcur
  ; field: waveform view follows the loaded loop; follower LED
  ksc changed gkNatSel
  gSNames[] fillarray @SNAMES@
  if ksc + kfirst > 0 then
    Slcd sprintfk "lcd_%d.png", limit(gkNatSel, 1, lenarray(gSNames))
    cabbageSet 1, "lcdText", "file", Slcd
  endif
  kvut metro 20
  if kvut == 1 then
    kvdl = dbamp(gkVuL + 0.000001)
    kvdr = dbamp(gkVuR + 0.000001)
@VU@
  endif
  krnd2 chnget "rndAll"
  krnt changed krnd2
  if krnt == 1 && kfirst == 0 then
@RND@
  endif
@SLAB@
  cabbageSet kled, "fLed", "alpha", 0.1 + 0.9 * gkFollow
  cabbageSet kled, "oLed", "alpha", 0.1 + 0.9 * gkOutEnv
  ; lester: little OLED read-out + inverted "A"/"B" when the overdrive is clipping
  kdsp metro 8
  if kdsp == 1 && ktab == 3 then
    SmA KXModeName gkAMode
    SmB KXModeName gkBMode
    SA sprintfk "%6d Hz   res %3d   %s", int(gkLP), int(gkRes * 100), SmA
    SB sprintfk "%6d Hz   res %3d   %s", int(gkBCut), int(gkBRes * 100), SmB
    cabbageSet kdsp, "lesA", "text", SA
    cabbageSet kdsp, "lesB", "text", SB
    kivA = (gkAGain > 0.5 ? 220 : 0)
    cabbageSet kdsp, "lesAn", "colour", kivA, kivA, kivA
    cabbageSet kdsp, "lesAn", "fontColour", 220 - kivA, 220 - kivA, 220 - kivA
    kivB = (gkBGain > 0.5 ? 220 : 0)
    cabbageSet kdsp, "lesBn", "colour", kivB, kivB, kivB
    cabbageSet kdsp, "lesBn", "fontColour", 220 - kivB, 220 - kivB, 220 - kivB
  endif
  ; lester: randomize (like the module's "Randomize current")
  krnd chnget "lRnd"
  krt changed krnd
  if krt == 1 && kfirst == 0 then
    cabbageSetValue "aMode", random:k(0, 4), krt
    cabbageSetValue "aGain", random:k(0.35, 0.85), krt
    cabbageSetValue "LPFreq", random:k(200, 9000), krt
    cabbageSetValue "Res", random:k(0, 0.9), krt
    cabbageSetValue "bCut", random:k(100, 12000), krt
    cabbageSetValue "bRes", random:k(0, 0.95), krt
    cabbageSetValue "bMode", random:k(0, 4), krt
    cabbageSetValue "bGain", random:k(0.35, 0.85), krt
    cabbageSetValue "lMix", random:k(0, 1), krt
    cabbageSetValue "link", int(random:k(1, 5.99)), krt
  endif
  cabbageSet kled, "l1Led", "alpha", 0.15 + 0.85 * (gkL1 * 0.5 + 0.5)
  cabbageSet kled, "l2Led", "alpha", 0.15 + 0.85 * (gkL2 * 0.5 + 0.5)
  cabbageSet kled, "vLed", "alpha", (active:k(11) > 0 ? 1 : 0.12)
  cabbageSet kled, "subLed", "alpha", 0.12 + 0.88 * gkSub
  kfirst = 0
endin

; ---------------------------------------------------------------------
;  instr 3 : nature generator ("Sampler - Nature"), always running
; ---------------------------------------------------------------------
instr 3
  ksel = gkNatSel
  aL = 0
  aR = 0

  if ksel == 1 then          ; ---- Wind
    an1 pinkish 1
    an2 pinkish 1
    kg randomi 0.15, 1, 0.12
    kg2 randomi 0.15, 1, 0.1
    kc randomi 220, 900, 0.08
    kwh randomi 0, 1, 0.05
    a1 butbp an1, kc, kc * 0.7
    a2 butbp an2, kc * 1.12, kc * 0.7
    aw1 butbp an1, kc * 2.6, 35
    aw2 butbp an2, kc * 2.9, 35
    aL = (a1 * 1.6 + aw1 * kwh * kwh * 6) * kg
    aR = (a2 * 1.6 + aw2 * kwh * kwh * 6) * kg2

  elseif ksel == 2 then      ; ---- Birds
    kt dust 1, 0.9
    if kt > 0 then
      kf random 2200, 4800
      kp random 0.1, 0.9
      kn random 2, 7
      kty random 0, 3
      event "i", 20, 0, 0.08 * kn + 0.05, kf, kp, kn, int(kty), 1
    endif
    an pinkish 0.15
    aL butbp an, 3000, 2000
    aR butbp an, 3300, 2000

  elseif ksel == 3 then      ; ---- Beach
    kph phasor 0.085
    kw = (1 - cos(2 * $M_PI * kph)) * 0.5
    kw2 = kw * kw
    kw4 = kw2 * kw2
    an1 noise 1, 0.3
    an2 noise 1, 0.3
    ab1 butlp an1, 250 + kw2 * 2600
    ab2 butlp an2, 280 + kw2 * 2400
    ac1 buthp an1, 3000
    ac2 buthp an2, 3200
    kdr randomi -0.3, 0.3, 0.05
    ac1 butlp ac1, 7000
    ac2 butlp ac2, 7000
    aL = (ab1 * (0.15 + kw * 0.8) + ac1 * kw4 * 0.12) * (1 - kdr)
    aR = (ab2 * (0.15 + kw * 0.8) + ac2 * kw4 * 0.12) * (1 + kdr)
    aL *= 0.3
    aR *= 0.3

  elseif ksel == 4 then      ; ---- Geiser
    ad1 dust2 1, 22
    ad2 dust2 1, 22
    kf1 randomh 140, 620, 30
    kf2 randomh 140, 620, 30
    ab1 reson ad1, kf1, kf1 * 0.15, 1
    ab2 reson ad2, kf2, kf2 * 0.15, 1
    an pinkish 0.08
    ah butbp an, 1800, 1500
    kt dust 1, 0.07
    if kt > 0 then
      event "i", 22, 0, 6 + rnd(4)
    endif
    aL = (ab1 * 0.5 + ah) * 2.5
    aR = (ab2 * 0.5 + ah) * 2.5

  elseif ksel == 5 then      ; ---- Forest
    ad1 dust2 1, 70
    ad2 dust2 1, 70
    kg randomi 0.1, 1, 0.2
    ar1 butbp ad1, 4200, 3000
    ar2 butbp ad2, 4500, 3000
    an pinkish 0.5
    aw butbp an, 400, 300
    kt dust 1, 0.06
    if kt > 0 then
      event "i", 23, 0, 1.5, random:k(0.15, 0.85)
    endif
    kb dust 1, 0.2
    if kb > 0 then
      event "i", 20, 0, 0.5, random:k(1400, 2600), random:k(0.1, 0.9), random:k(2, 4), 2, 0.4
    endif
    aL = ar1 * kg * 0.6 + aw * 0.5
    aR = ar2 * kg * 0.6 + aw * 0.5

  elseif ksel == 6 then      ; ---- Water
    an1 pinkish 1
    an2 pinkish 1
    ab1 butbp an1, 1100, 900
    ab2 butbp an2, 1300, 900
    ad1 dust2 1, 45
    ad2 dust2 1, 45
    kf1 randomh 500, 2400, 60
    kf2 randomh 500, 2400, 60
    abl1 reson ad1, kf1, 40, 1
    abl2 reson ad2, kf2, 40, 1
    aL = ab1 * 0.35 + abl1 * 0.45
    aR = ab2 * 0.35 + abl2 * 0.45

  elseif ksel == 7 then      ; ---- Thunder (rain + rumbles)
    ad1 dust2 1, 900
    ad2 dust2 1, 900
    ar1 buthp ad1, 1800
    ar2 buthp ad2, 1800
    an pinkish 0.4
    aw butlp an, 900
    kt dust 1, 0.055
    kinit init 1
    if kt > 0 || kinit == 1 then
      event "i", 21, (kinit == 1 ? 1.5 : 0), 9 + rnd(5)
    endif
    kinit = 0
    aL = ar1 * 0.08 + aw * 0.45
    aR = ar2 * 0.08 + aw * 0.45

  elseif ksel == 8 then      ; ---- Night (crickets)
    kph1 phasor 1.25
    kph2 phasor 1.07
    kph3 phasor 0.83
    kg1 = (kph1 < 0.28 ? 1 : 0)
    kg2 = (kph2 < 0.22 ? 1 : 0)
    kg3 = (kph3 < 0.35 ? 1 : 0)
    kg1 portk kg1, 0.008
    kg2 portk kg2, 0.008
    kg3 portk kg3, 0.008
    ap1 poscil 1, 28
    ap2 poscil 1, 33
    ap3 poscil 1, 24
    ac1 poscil 0.5, 4400
    ac2 poscil 0.5, 4750
    ac3 poscil 0.35, 3900
    ac1 = ac1 * (ap1 * 0.5 + 0.5) * kg1
    ac2 = ac2 * (ap2 * 0.5 + 0.5) * kg2
    ac3 = ac3 * (ap3 * 0.5 + 0.5) * kg3
    an pinkish 0.3
    aw butlp an, 300
    aL = (ac1 * 0.8 + ac2 * 0.3 + ac3 * 0.5) * 0.12 + aw
    aR = (ac1 * 0.3 + ac2 * 0.8 + ac3 * 0.5) * 0.12 + aw
  endif

  gaNatL += aL
  gaNatR += aR
endin

; ---------------------------------------------------------------------
;  instr 4 : VCA INIT drone (the original's VCA offset)
; ---------------------------------------------------------------------
instr 4
  if gkInit < 0.001 kgoto skip
  kch changed gkWave
  if kch == 1 then
    reinit RESTART
  endif
RESTART:
  iwave = round(i(gkWave))
  kcps = cpsmidinn(gkLastPitch + gkVCO + gkOct + 12 * log2(max(gkTune, 0.01)))
  kcps portk kcps, 0.05
  kcps limit kcps, 4, sr * 0.45
  aL, aR KXUni kcps, gkPW, gkDetune, gkSpread, gkDrift, iwave, 2, 0
  rireturn
  aL = tanh(aL * gkAmpVCO * 0.35)
  aR = tanh(aR * gkAmpVCO * 0.35)
  kcf limit gkLP * 2 ^ (gkL1 * 0.5), 25, sr * 0.42
  aL moogladder2 aL, kcf, gkRes
  aR moogladder2 aR, kcf, gkRes
  kamp portk gkInit, 0.05
  gaVL += aL * kamp * 0.25
  gaVR += aR * kamp * 0.25
  gaRevL += aL * kamp * 0.25
  gaRevR += aR * kamp * 0.25
skip:
endin

; ---------------------------------------------------------------------
  ;  instr 50 : master  (drive -> chorus -> delay -> reverb -> output)
; ---------------------------------------------------------------------
instr 50
  ; nature level and envelope (for the "Nature" mod source)
  aNL = gaNatL
  aNR = gaNatR
  gaNatPrev = (aNL + aNR) * 0.5
  knr rms gaNatPrev, 4
  gkNatEnv limit knr * 7, 0, 1
  kns portk (gkNatSel <= 8 ? 2.6 * (1 - exp(-gkSamp * 160 / 2.6)) : 0), 0.05
  aNL *= kns
  aNR *= kns

  ; drive
  ; (drive is applied per voice now; the buses pass through clean)
  aL = gaVL
  aR = gaVR
  aDL = gaDlyL
  aDR = gaDlyR
  aRL = gaRevL
  aRR = gaRevR

  ; chorus / ensemble
  kch portk gkChorus, 0.02
  if kch > 0.001 then
    am1 poscil 1, 0.31, giSine
    am2 poscil 1, 0.47, giSine, 0.33
    am3 poscil 1, 0.23, giSine, 0.66
    adp = 2 + kch * 5
    ac1 vdelay3 aL, 11 + am1 * adp, 50
    ac2 vdelay3 aR, 13 + am2 * adp, 50
    ac3 vdelay3 (aL + aR) * 0.5, 17 + am3 * adp, 50
    aL = aL * (1 - kch * 0.45) + (ac1 * 0.7 + ac3 * 0.4) * kch
    aR = aR * (1 - kch * 0.45) + (ac2 * 0.7 - ac3 * 0.4) * kch
  endif

  ; ping-pong delay, tempo synced, wobbly tape-ish feedback
  kdiv tab round(gkDlyTime) - 1, 901
  kdt = kdiv * 60 / gkBPM
  kdt limit kdt, 0.01, 2.9
  adt interp kdt
  adt = adt * 1000
  awob poscil 0.6, 0.6
  aFbL init 0
  aFbR init 0
  kdm portk gkDlyMix, 0.02
  aIn = (aDL + aDR) * 0.5 + (aNL + aNR) * 0.15
  aTapL vdelay3 aIn * kdm + aFbR, adt + awob, 3000
  aTapR vdelay3 aFbL, adt + awob, 3000
  aFbL = tanh(butlp(aTapL, 4200) * gkDlyFb)
  aFbR = tanh(butlp(aTapR, 4200) * gkDlyFb)
  aL += aTapL
  aR += aTapR

  ; reverb (original "reverb" = amount; "space" = size)
  krv portk gkRev, 0.02
  ksp portk gkSpace, 0.05
  kfb = 0.72 + ksp * 0.25
  kfc = 3500 + ksp * 9000
  arvL, arvR reverbsc aRL + aTapL * 0.5 + aNL * 0.8 + gaFieldL * 0.5, aRR + aTapR * 0.5 + aNR * 0.8 + gaFieldR * 0.5, kfb, kfc
  kwet = krv * 1.7
#ifdef SONIC
  ; ---- FX returns and the nature bed are points too (wider: lower orders)
  aL = aL + arvL * kwet
  aR = aR + arvR * kwet
  SpPoint aL, gkPX[18], gkPY[18], gkPZ[18], 0.55 + gkSpSpread * 0.45, gkSpAir
  SpPoint aR, gkPX[19], gkPY[19], gkPZ[19], 0.55 + gkSpSpread * 0.45, gkSpAir
  SpPoint aNL, gkPX[20], gkPY[20], gkPZ[20], 0.35 + gkSpSpread * 0.65, gkSpAir
  SpPoint aNR, gkPX[21], gkPY[21], gkPZ[21], 0.35 + gkSpSpread * 0.65, gkSpAir
  ; ---- 16-channel output: level, linked peak limiter driven by the omni (W) channel
  kvol portk gkVol / 3, 0.02
  aW = gaAmb[0] * kvol
  kpk max_k aW, 1, 1
  klim init 0
  klim = (kpk > klim ? kpk : klim * 0.975)
  kgl = (klim > 0.9 ? 0.9 / klim : 1)
  kgl portk kgl, 0.003
  kgo = kvol * kgl
  a0 dcblock2 gaAmb[0] * kgo
  a1 = gaAmb[1] * kgo
  a2 = gaAmb[2] * kgo
  a3 = gaAmb[3] * kgo
  a4 = gaAmb[4] * kgo
  a5 = gaAmb[5] * kgo
  a6 = gaAmb[6] * kgo
  a7 = gaAmb[7] * kgo
  a8 = gaAmb[8] * kgo
  a9 = gaAmb[9] * kgo
  a10 = gaAmb[10] * kgo
  a11 = gaAmb[11] * kgo
  a12 = gaAmb[12] * kgo
  a13 = gaAmb[13] * kgo
  a14 = gaAmb[14] * kgo
  a15 = gaAmb[15] * kgo
  ; 16-bit output on every channel
  adth rand 0.5
  a0 = round(a0 * 32767 + adth) / 32767
  a1 = round(a1 * 32767 + adth) / 32767
  a2 = round(a2 * 32767 + adth) / 32767
  a3 = round(a3 * 32767 + adth) / 32767
  a4 = round(a4 * 32767 + adth) / 32767
  a5 = round(a5 * 32767 + adth) / 32767
  a6 = round(a6 * 32767 + adth) / 32767
  a7 = round(a7 * 32767 + adth) / 32767
  a8 = round(a8 * 32767 + adth) / 32767
  a9 = round(a9 * 32767 + adth) / 32767
  a10 = round(a10 * 32767 + adth) / 32767
  a11 = round(a11 * 32767 + adth) / 32767
  a12 = round(a12 * 32767 + adth) / 32767
  a13 = round(a13 * 32767 + adth) / 32767
  a14 = round(a14 * 32767 + adth) / 32767
  a15 = round(a15 * 32767 + adth) / 32767
  outch 1, a0, 2, a1, 3, a2, 4, a3, 5, a4, 6, a5, 7, a6, 8, a7, 9, a8, 10, a9, 11, a10, 12, a11, 13, a12, 14, a13, 15, a14, 16, a15
  ; a virtual cardioid pair (left / right) for the meters, the scopes and the followers
  aL = (a0 + a1) * 0.5
  aR = (a0 - a1) * 0.5
  gaOutPrev = a0
  gkVuL rms aL, 12
  gkVuR rms aR, 12
  ki = 0
  while ki < 16 do
    gaAmb[ki] = 0
    ki += 1
  od
#else
  aL = aL + aNL + arvL * kwet + gaFieldL
  aR = aR + aNR + arvR * kwet + gaFieldR

  ; output level + safety
  kvol portk gkVol / 3, 0.02
  aL = aL * kvol
  aR = aR * kvol
  aL dcblock2 aL
  aR dcblock2 aR
  ; transparent linked peak limiter (fast attack, 150 ms release) instead of a waveshaper + hard clip
  kpkl max_k aL, 1, 1
  kpkr max_k aR, 1, 1
  kpk = max(kpkl, kpkr)
  klim init 0
  klim = (kpk > klim ? kpk : klim * 0.97)
  kgl = (klim > 0.89 ? 0.89 / klim : 1)
  agl interp kgl
  agl tone agl, 400
  aL = aL * agl
  aR = aR * agl
  aL clip aL, 0, 0.99
  aR clip aR, 0, 0.99
  ; 16-bit output: quantised to 65536 levels, with half a step of dither
  adth rand 0.5
  aL = round(aL * 32767 + adth) / 32767
  aR = round(aR * 32767 - adth) / 32767
  outs aL, aR
  gaOutPrev = (aL + aR) * 0.5
  gkVuL rms aL, 12
  gkVuR rms aR, 12
#end

  ; Odessa-style 12-band power spectrum LEDs (0.8 oct bands)
  if gkTab == 2 then
    kspt metro 15
    am = gaOutPrev
    ab1 butbp am, 25, 20
    ab2 butbp am, 47, 30
    ab3 butbp am, 84, 50
    ab4 butbp am, 152, 90
    ab5 butbp am, 274, 160
    ab6 butbp am, 492, 290
    ab7 butbp am, 885, 520
    ab8 butbp am, 1590, 940
    ab9 butbp am, 2860, 1700
    ab10 butbp am, 5160, 3000
    ab11 butbp am, 9300, 5400
    ab12 butbp am, 15000, 7000
    kb1 rms ab1, 10
    kb2 rms ab2, 10
    kb3 rms ab3, 10
    kb4 rms ab4, 10
    kb5 rms ab5, 10
    kb6 rms ab6, 10
    kb7 rms ab7, 10
    kb8 rms ab8, 10
    kb9 rms ab9, 10
    kb10 rms ab10, 10
    kb11 rms ab11, 10
    kb12 rms ab12, 10
    cabbageSet kspt, "sp1", "alpha", limit(1 + dbamp(kb1 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp2", "alpha", limit(1 + dbamp(kb2 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp3", "alpha", limit(1 + dbamp(kb3 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp4", "alpha", limit(1 + dbamp(kb4 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp5", "alpha", limit(1 + dbamp(kb5 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp6", "alpha", limit(1 + dbamp(kb6 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp7", "alpha", limit(1 + dbamp(kb7 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp8", "alpha", limit(1 + dbamp(kb8 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp9", "alpha", limit(1 + dbamp(kb9 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp10", "alpha", limit(1 + dbamp(kb10 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp11", "alpha", limit(1 + dbamp(kb11 + 0.00001) / 48, 0.06, 1)
    cabbageSet kspt, "sp12", "alpha", limit(1 + dbamp(kb12 + 0.00001) / 48, 0.06, 1)
  endif

  adisplay = (aL + aR) * 0.5
  display adisplay, 0.05, 1

  kact active 1
  if kact > 0 then
    adispX = gaDispX / kact
    adispY = gaDispY / kact
  else
    adispX = gaPrevX
    adispY = gaPrevY
  endif
  adispX = adispX * 0.92
  adispY = adispY * -0.92
  display adispX, 0.04, 1
  display adispY, 0.04, 1
  ; LFO and Lorenz scopes: Cabbage can't show a 2 s display window, so the last 2 s of each
  ; signal are kept in a 256-point history and scanned 20 times a second (oldest left, newest right)
  kscw init 0
  ksct metro 128
  if ksct == 1 then
    tablew gkL1 * 0.9, kscw, giScL1
    tablew gkL2 * 0.9, kscw, giScL2
        kscw = (kscw + 1) % 256
  endif
  ascp phasor 20
  ; freeze the history's start at the beginning of each scan, so the trace never tears mid-screen
  kscp downsamp ascp
  kscpp init 1
  kscr init 0
  if kscp < kscpp then
    kscr = kscw
  endif
  kscpp = kscp
  ascx = ascp * 256 + kscr
  alfo1 tablei ascx, giScL1, 0, 0, 1
  alfo2 tablei ascx, giScL2, 0, 0, 1
  display alfo1, 0.05, 1
  display alfo2, 0.05, 1
  gaDispX = 0
  gaDispY = 0

  gaVL = 0
  gaVR = 0
  gaDlyL = 0
  gaDlyR = 0
  gaRevL = 0
  gaRevR = 0
  gaNatL = 0
  gaNatR = 0
  gaFieldL = 0
  gaFieldR = 0
endin
giDly ftgen 901, 0, 16, -2, 0.125, 0.1666667, 0.25, 0.3333333, 0.5, 0.75, 1, 1.5, 2

; ---------------------------------------------------------------------
;  nature events
; ---------------------------------------------------------------------
instr 20 ; bird chirp: p4 freq, p5 pan, p6 syllables, p7 type, p8 level
  isyl = p6 / max(p3 - 0.05, 0.05)
  kph phasor isyl
  kenv = sin($M_PI * kph)
  kenv = kenv * kenv
  kov linseg 0, 0.01, 1, p3 - 0.04, 1, 0.03, 0
  if p7 == 0 then
    kf = p4 * (1 + 0.5 * (1 - kph))
  elseif p7 == 1 then
    kf = p4 * (0.7 + 0.6 * kph)
  else
    kf = p4 * (1 + 0.15 * sin(2 * $M_PI * kph * 3))
  endif
  kvib poscil 0.03, 38
  a1 poscil kenv * kov * 0.09 * p8, kf * (1 + kvib)
  gaNatL += a1 * sqrt(1 - p5)
  gaNatR += a1 * sqrt(p5)
endin

instr 21 ; thunder rumble
  an pinkish 1
  kcrk expseg 1, 0.4, 0.05, p3, 0.001
  kenv linseg 0, 0.15, 1, p3 * 0.3, 0.7, p3 * 0.7 - 0.15, 0
  kroll randomi 0.3, 1, 3
  alo butlp an, 110 + kroll * 90
  alo butlp alo, 160
  ahi butbp an, 900, 800
  a1 = (alo * 4 * kroll + ahi * kcrk * 0.6) * kenv
  kp randomi 0.2, 0.8, 0.2
  gaNatL += a1 * sqrt(1 - kp)
  gaNatR += a1 * sqrt(kp)
endin

instr 22 ; geyser eruption
  an noise 1, 0
  kenv linseg 0, p3 * 0.35, 1, p3 * 0.65, 0
  kc expseg 400, p3 * 0.4, 3500, p3 * 0.6, 900
  a1 butbp an, kc, kc
  ab dust2 1, 60 * kenv + 1
  ab reson ab, 300 + kenv * 500, 80, 1
  gaNatL += (a1 * 0.25 + ab * 0.2) * kenv
  gaNatR += (a1 * 0.25 + ab * 0.2) * kenv
endin

instr 23 ; woodpecker
  irate random 13, 18
  kt metro irate
  kenv linseg 1, p3, 0.2
  ai = a(kt)
  ak reson ai, 950, 300, 1
  ak2 reson ai, 2100, 400, 1
  a1 = (ak + ak2 * 0.5) * kenv * 0.6
  gaNatL += a1 * sqrt(1 - p4)
  gaNatR += a1 * sqrt(p4)
endin

; ---------------------------------------------------------------------
;  instr 6 : field recordings - lazy loader, ambient bed, audio followers
; ---------------------------------------------------------------------

#ifdef SONIC
; ---------------------------------------------------------------------
;  instr 5 : the motion system for the 22 spatial points
;  flock (3-D boids)  >  deviated Lorenz (one attractor per point, each
;  with its own constants and turned to its own heading)  >  gravity
;  (points falling round three orbiting wells). MODE morphs across them.
; ---------------------------------------------------------------------
instr 5
  iN = 22
  kFX[] init 22
  kFY[] init 22
  kFZ[] init 22
  kVX[] init 22
  kVY[] init 22
  kVZ[] init 22
  kLX[] init 22
  kLY[] init 22
  kLZ[] init 22
  kGX[] init 22
  kGY[] init 22
  kGZ[] init 22
  kHX[] init 22
  kHY[] init 22
  kHZ[] init 22
  kOX[] init 22
  kOY[] init 22
  kOZ[] init 22
  kQX[] init 22
  kQY[] init 22
  kQZ[] init 22
  kWX[] init 22
  kWY[] init 22
  kWZ[] init 22
  kDS[] init 22
  kDR[] init 22
  kinit init 1
  if kinit == 1 then
    ki = 0
    while ki < iN do
      ka = ki * 2.39996
      kFX[ki] = cos(ka) * 0.6
      kFY[ki] = sin(ka) * 0.6
      kFZ[ki] = random:k(-0.3, 0.3)
      kVX[ki] = random:k(-0.1, 0.1)
      kVY[ki] = random:k(-0.1, 0.1)
      kVZ[ki] = random:k(-0.05, 0.05)
      kLX[ki] = random:k(-8, 8)
      kLY[ki] = random:k(-8, 8)
      kLZ[ki] = random:k(18, 32)
      kGX[ki] = cos(ka) * 0.7
      kGY[ki] = sin(ka) * 0.7
      kGZ[ki] = random:k(-0.2, 0.2)
      kHX[ki] = -sin(ka) * 0.3
      kHY[ki] = cos(ka) * 0.3
      kHZ[ki] = 0
      kDS[ki] = random:k(-1, 1)
      kDR[ki] = random:k(-1, 1)
      gkTX[ki] = kFX[ki] * gkSpDist
      gkTY[ki] = kFY[ki] * gkSpDist
      gkTZ[ki] = 0
      gkPX[ki] = gkTX[ki]
      gkPY[ki] = gkTY[ki]
      gkPZ[ki] = 0
      ki += 1
    od
    kinit = 0
  endif

  kup metro 40
  if kup == 1 then
    idt = 0.025
    kspd = 0.08 + gkSpSpeed * 1.4
    kdev = gkSpDev
    ; ---- flock
    kcx = 0
    kcy = 0
    kcz = 0
    kmx = 0
    kmy = 0
    kmz = 0
    ki = 0
    while ki < iN do
      kcx += kFX[ki]
      kcy += kFY[ki]
      kcz += kFZ[ki]
      kmx += kVX[ki]
      kmy += kVY[ki]
      kmz += kVZ[ki]
      ki += 1
    od
    kldt init 0
    kldt += idt * (0.08 + gkSpSpeed * 0.7)
    kldx = 0.72 * cos(kldt)
    kldy = 0.72 * sin(kldt * 1.13)
    kldz = 0.35 * sin(kldt * 0.61)
    kcx /= iN
    kcy /= iN
    kcz /= iN
    kmx /= iN
    kmy /= iN
    kmz /= iN
    ki = 0
    while ki < iN do
      ksx = 0
      ksy = 0
      ksz = 0
      kj = 0
      while kj < iN do
        if kj != ki then
          kdx = kFX[ki] - kFX[kj]
          kdy = kFY[ki] - kFY[kj]
          kdz = kFZ[ki] - kFZ[kj]
          kd2 = kdx * kdx + kdy * kdy + kdz * kdz
          if kd2 < 0.1 then
            kiv = 1 / (kd2 + 0.02)
            ksx += kdx * kiv
            ksy += kdy * kiv
            ksz += kdz * kiv
          endif
        endif
        kj += 1
      od
      kcoh = 0.2 + gkSpCoh * 1.6
      ; cohesion pulls half to the flock's centre, half to the leader circling the listener
      ktx = (kcx + kldx) * 0.5
      kty = (kcy + kldy) * 0.5
      ktz = (kcz + kldz) * 0.5
      kax = (ktx - kFX[ki]) * kcoh + ksx * 0.025 + (kmx - kVX[ki]) * 0.8 + random:k(-1, 1) * 0.6 * kspd
      kay = (kty - kFY[ki]) * kcoh + ksy * 0.025 + (kmy - kVY[ki]) * 0.8 + random:k(-1, 1) * 0.6 * kspd
      kaz = (ktz - kFZ[ki]) * kcoh + ksz * 0.025 + (kmz - kVZ[ki]) * 0.8 + random:k(-1, 1) * 0.4 * kspd
      kpr = sqrt(kFX[ki] * kFX[ki] + kFY[ki] * kFY[ki] + kFZ[ki] * kFZ[ki])
      if kpr > 1 then
        kax -= kFX[ki] * (kpr - 1) * 6
        kay -= kFY[ki] * (kpr - 1) * 6
        kaz -= kFZ[ki] * (kpr - 1) * 6
      elseif kpr < 0.35 then
        kpi = (0.35 - kpr) * 4 / max(kpr, 0.05)
        kax += kFX[ki] * kpi
        kay += kFY[ki] * kpi
        kaz += kFZ[ki] * kpi
      endif
      ; a slow swirl so the flock circles round you rather than parking
      kax += -kFY[ki] * 0.25 * kspd
      kay += kFX[ki] * 0.25 * kspd
      kVX[ki] = kVX[ki] + kax * idt
      kVY[ki] = kVY[ki] + kay * idt
      kVZ[ki] = kVZ[ki] + kaz * idt
      kv = sqrt(kVX[ki] * kVX[ki] + kVY[ki] * kVY[ki] + kVZ[ki] * kVZ[ki])
      if kv > kspd then
        kVX[ki] = kVX[ki] * kspd / kv
        kVY[ki] = kVY[ki] * kspd / kv
        kVZ[ki] = kVZ[ki] * kspd / kv
      endif
      kFX[ki] = kFX[ki] + kVX[ki] * idt
      kFY[ki] = kFY[ki] + kVY[ki] * idt
      kFZ[ki] = kFZ[ki] + kVZ[ki] * idt
      ki += 1
    od
    ; ---- deviated Lorenz: every point its own attractor
    kldt = (0.0015 + gkSpSpeed * 0.012) * 1.25
    ki = 0
    while ki < iN do
      ksg = 10 * (1 + kDS[ki] * kdev * 0.4)
      kro = 28 * (1 + kDR[ki] * kdev * 0.3)
      kst = 0
      while kst < 4 do
        klx = kLX[ki]
        kly = kLY[ki]
        klz = kLZ[ki]
        kLX[ki] = klx + ksg * (kly - klx) * kldt
        kLY[ki] = kly + (klx * (kro - klz) - kly) * kldt
        kLZ[ki] = klz + (klx * kly - 2.6667 * klz) * kldt
        kst += 1
      od
      khd = ki * 6.2832 / iN * (0.15 + kdev * 0.85)
      kux = kLX[ki] / 13
      kuy = kLY[ki] / 15
      kHX[ki] = kux * cos(khd) - kuy * sin(khd)
      kHY[ki] = kux * sin(khd) + kuy * cos(khd)
      kHZ[ki] = (kLZ[ki] - 25) / 15
      ki += 1
    od
    ; ---- gravity: three wells on slow orbits
    kwt init 0
    kwt += idt * (0.05 + gkSpSpeed * 0.4)
    kw1x = 0.75 * cos(kwt)
    kw1y = 0.75 * sin(kwt)
    kw1z = 0.3 * sin(kwt * 0.7)
    kw2x = 0.6 * cos(-kwt * 1.37 + 2.1)
    kw2y = 0.6 * sin(-kwt * 1.37 + 2.1)
    kw2z = -0.35 * cos(kwt * 0.53)
    kw3x = 0.4 * cos(kwt * 0.61 + 4.2)
    kw3y = 0.85 * sin(kwt * 0.61 + 4.2)
    kw3z = 0.5 * sin(kwt * 1.1 + 1)
    kgg = 0.05 + gkSpGrav * 0.6
    ki = 0
    while ki < iN do
      kax = 0
      kay = 0
      kaz = 0
      kdx = kw1x - kGX[ki]
      kdy = kw1y - kGY[ki]
      kdz = kw1z - kGZ[ki]
      kd3 = (kdx * kdx + kdy * kdy + kdz * kdz + 0.04) ^ 1.5
      kax += kdx / kd3
      kay += kdy / kd3
      kaz += kdz / kd3
      kdx = kw2x - kGX[ki]
      kdy = kw2y - kGY[ki]
      kdz = kw2z - kGZ[ki]
      kd3 = (kdx * kdx + kdy * kdy + kdz * kdz + 0.04) ^ 1.5
      kax += kdx / kd3
      kay += kdy / kd3
      kaz += kdz / kd3
      kdx = kw3x - kGX[ki]
      kdy = kw3y - kGY[ki]
      kdz = kw3z - kGZ[ki]
      kd3 = (kdx * kdx + kdy * kdy + kdz * kdz + 0.04) ^ 1.5
      kax += kdx / kd3
      kay += kdy / kd3
      kaz += kdz / kd3
      kQX[ki] = (kQX[ki] + kax * kgg * idt) * 0.9985
      kQY[ki] = (kQY[ki] + kay * kgg * idt) * 0.9985
      kQZ[ki] = (kQZ[ki] + kaz * kgg * idt) * 0.9985
      kv = sqrt(kQX[ki] * kQX[ki] + kQY[ki] * kQY[ki] + kQZ[ki] * kQZ[ki])
      kvm = kspd * 1.6
      if kv > kvm then
        kQX[ki] = kQX[ki] * kvm / kv
        kQY[ki] = kQY[ki] * kvm / kv
        kQZ[ki] = kQZ[ki] * kvm / kv
      endif
      kGX[ki] = kGX[ki] + kQX[ki] * idt
      kGY[ki] = kGY[ki] + kQY[ki] * idt
      kGZ[ki] = kGZ[ki] + kQZ[ki] * idt
      kpr = sqrt(kGX[ki] * kGX[ki] + kGY[ki] * kGY[ki] + kGZ[ki] * kGZ[ki])
      if kpr > 1.1 then
        kGX[ki] = kGX[ki] * 1.1 / kpr
        kGY[ki] = kGY[ki] * 1.1 / kpr
        kGZ[ki] = kGZ[ki] * 1.1 / kpr
        kQX[ki] = kQX[ki] * 0.5
        kQY[ki] = kQY[ki] * 0.5
        kQZ[ki] = kQZ[ki] * 0.5
      endif
      ki += 1
    od
    ; ---- deviation: every point wanders off on its own
    kyaw init 0
    kyaw += idt * gkSpRot * 0.6283
    kmd = gkSpMode
    kwF limit 1 - kmd, 0, 1
    kwL limit 1 - abs(kmd - 1), 0, 1
    kwG limit kmd - 1, 0, 1
    knb = 1 / sqrt(kwF * kwF + kwL * kwL + kwG * kwG + 0.0001)   ; blending two motions must not shrink them
    kwF *= knb
    kwL *= knb
    kwG *= knb
    ki = 0
    while ki < iN do
      if random:k(0, 1) < 0.01 + gkSpSpeed * 0.025 then
        kWX[ki] = random:k(-1, 1)
        kWY[ki] = random:k(-1, 1)
        kWZ[ki] = random:k(-1, 1)
      endif
      kOX[ki] = kOX[ki] + (kWX[ki] - kOX[ki]) * 0.02
      kOY[ki] = kOY[ki] + (kWY[ki] - kOY[ki]) * 0.02
      kOZ[ki] = kOZ[ki] + (kWZ[ki] - kOZ[ki]) * 0.02
      ki += 1
    od
    kfcx = 0
    kfcy = 0
    kfcz = 0
    ki = 0
    while ki < iN do
      kx = kwF * kFX[ki] + kwL * kHX[ki] + kwG * kGX[ki]
      ky = kwF * kFY[ki] + kwL * kHY[ki] + kwG * kGY[ki]
      kz = kwF * kFZ[ki] + kwL * kHZ[ki] + kwG * kGZ[ki]
      ; each point's own slow wander (deviation)
      kx = kx + kOX[ki] * kdev * 0.35
      ky = ky + kOY[ki] * kdev * 0.35
      kz = kz + kOZ[ki] * kdev * 0.25
      kz = kz * gkSpHeight
      krx = kx * cos(kyaw) - ky * sin(kyaw)
      kry = kx * sin(kyaw) + ky * cos(kyaw)
      gkTX[ki] = krx * gkSpDist
      gkTY[ki] = kry * gkSpDist
      gkTZ[ki] = kz * gkSpDist
      if ki >= 12 && ki < 18 then
        kfcx += gkTX[ki] / 6
        kfcy += gkTY[ki] / 6
        kfcz += gkTZ[ki] / 6
      endif
      ki += 1
    od
    ; field copies: FIELD SPLAY scatters them from their own centre (0 = one cloud, 1 = all over)
    ksp = 0.15 + gkSpFSplay * 1.1
    ki = 12
    while ki < 18 do
      gkTX[ki] = kfcx + (gkTX[ki] - kfcx) * ksp
      gkTY[ki] = kfcy + (gkTY[ki] - kfcy) * ksp
      gkTZ[ki] = kfcz + (gkTZ[ki] - kfcz) * ksp
      ki += 1
    od
  endif
  ; glide every point to its target (no zipper in the encoder gains)
  ki = 0
  while ki < 22 do
    gkPX[ki] = gkPX[ki] + (gkTX[ki] - gkPX[ki]) * 0.016
    gkPY[ki] = gkPY[ki] + (gkTY[ki] - gkPY[ki]) * 0.016
    gkPZ[ki] = gkPZ[ki] + (gkTZ[ki] - gkPZ[ki]) * 0.016
    ki += 1
  od
endin

; ---------------------------------------------------------------------
;  instr 7 : one copy of the field recording (six run), each with its own
;  slowly wandering loop start and end, each its own point in space
; ---------------------------------------------------------------------
instr 7
  icp = p4
  kch changed gkFTabL, gkFRev
  if kch == 1 then
    reinit FCOPY
  endif
FCOPY:
  itl = i(gkFTabL)
  itr = i(gkFTabR)
  ilen = i(gkFLen)
  a1 = 0
  if itl <= 0 || ilen <= 0.05 goto FSKIP
  imode = (i(gkFRev) > 0.5 ? 1 : 0)
  ifn = (icp % 2 == 0 ? itl : itr)
  iph random 0, 0.9
  kA rspline 0, 1, 0.18 / (@NIDLE@ * giIdleStep), 1.2 / (@NIDLE@ * giIdleStep)
  kB rspline 0, 1, 0.18 / (@NIDLE@ * giIdleStep), 1.2 / (@NIDLE@ * giIdleStep)
  kst = kA * 0.7 * ilen
  ken = min(ilen, kst + (0.12 + kB * 0.6) * ilen)
  kfp = gkFSpeed * gkFSrFix * (1 + (icp - 2.5) * 0.003 * gkSpDev)
  a1 flooper2 1, kfp, kst, ken, 0.2, ifn, iph * ilen, imode
FSKIP:
  rireturn
  kon = (gkNatSel > 8 ? 1 : 0)
  kbl portk kon * 0.6 * (1 - exp(-gkSamp * 25 / 0.6)), 0.02
  if kbl < 0.0002 kgoto FC_END              ; sampler off: this copy costs nothing
  a1 = a1 * kbl * 0.62 * gkFNorm
  ip = 12 + icp
  SpPoint a1, gkPX[ip], gkPY[ip], gkPZ[ip], gkSpSpread, gkSpAir
FC_END:
endin
#end

gSFiles[] fillarray @FILES@
giFNorm[] fillarray @FNORM@          ; loudness-matching gain of each recording
giNFiles = lenarray(gSFiles)

instr 6
  if gkNatSel > 8 then
    gkFRec = gkNatSel - 8
  endif
  ksel limit round(gkFRec), 1, giNFiles
  kch changed ksel, gkFRev
  kfirst init 1
  if kch == 1 || kfirst == 1 then
    reinit LOAD
  endif
  kfirst = 0
LOAD:
  isel limit i(ksel), 1, giNFiles
  if giFLoaded[isel] == 0 then
    Sdir chnget "CSD_PATH"
    Sf sprintf "%s/samples/%s.wav", Sdir, gSFiles[isel - 1]
    itl ftgen 0, 0, 0, 1, Sf, 0, 0, 1
    itr ftgen 0, 0, 0, 1, Sf, 0, 0, 2
    giFTabL[isel] = itl
    giFTabR[isel] = itr
    giFLen[isel] = ftlen(itl) / sr
    giFLoaded[isel] = 1
  endif
  itl = giFTabL[isel]
  itr = giFTabR[isel]
  gkFTabL init itl
  gkFTabR init itr
  gkFLen init giFLen[isel]
  gkFNorm init giFNorm[isel - 1]
  gkFSrFix init ftsr(itl) / sr
  imode = (i(gkFRev) > 0.5 ? 1 : 0)
  ilen = giFLen[isel]
  kbs = gkFSpeed * gkFSrFix
  ; drifting loop window: start wanders the first half, length 30-80% of the file
  kbst = gkLpA * 0.5 * ilen
  kben = min(ilen, kbst + (0.3 + gkLpB * 0.5) * ilen)
  aBL flooper2 1, kbs, kbst, kben, 0.25, itl, 0, imode
  aBR flooper2 1, kbs, kbst, kben, 0.25, itr, 0, imode
  rireturn

  ; follower of the stock audio (bed + the keyboard-played layer)
  kon = (gkNatSel > 8 ? 1 : 0)
  araw = (aBL + aBR) * 0.5 * kon + gaNatPrev + gaFieldRaw
  kfr rms araw, 30
  ktg limit sqrt(kfr * gkFGain * 6), 0, 1
  kfol init 0
  kca = 1 - exp(-ksmps / (sr * max(gkFAtt, 0.001)))
  kcr = 1 - exp(-ksmps / (sr * max(gkFRel, 0.005)))
  kfol = kfol + (ktg - kfol) * (ktg > kfol ? kca : kcr)
  gkFollow = kfol
  ; follower of the instrument's own output
  kor rms gaOutPrev, 30
  kot limit sqrt(kor * 5), 0, 1
  koe init 0
  koe = koe + (kot - koe) * (kot > koe ? kca : kcr)
  gkOutEnv = koe

  kbl portk kon * 0.6 * (1 - exp(-gkSamp * 25 / 0.6)) * gkFNorm, 0.02
  gaFieldL += aBL * kbl
  gaFieldR += aBR * kbl
  gaFieldRaw = 0
endin
schedule 6, 0, -1
#ifdef SONIC
schedule 5, 0, -1
schedule 7, 0, -1, 0
schedule 7, 0, -1, 1
schedule 7, 0, -1, 2
schedule 7, 0, -1, 3
schedule 7, 0, -1, 4
schedule 7, 0, -1, 5
#end

schedule 2, 0, -1
schedule 3, 0, -1
schedule 50, 0, -1
