// ObliqSound / ObliqSonic SynthDefs. Compiled headless by sclang (see build_sc.sh): argv[0] = output folder.
//
// A voice is a group of small synths on a private stereo bus (vbus):
//   ovOsc<wave>   the oscillator stack: unison VCO, sub, FM pair, wavefolder, noise
//   ovPoly        polygonal oscillator             (only made if its level is up at note-on)
//   ovOde<n>      additive bank, n = 1 / 3 / 5 chord voices (same)
//   ovField       the field recording played from the keys (same)
//   ovFilt<link>  the dual morphing filter, amp, drive and the sends (always last in the group)
// Every modulated value comes from the voice's control-bus block (kb), which the plug-in writes
// directly once per 64-sample block: envelopes, LFOs, the matrix and the swarm are all computed in C++.
(
var out = thisProcess.argv[0];
var lag = 0.004;
// ---- layout of a voice's control block (keep in step with VoiceBus in Engine.h)
var kFreq = 0, kPw = 1, kDetune = 2, kDrift = 3, kSpread = 4, kVco = 5, kSub = 6, kSub2 = 7, kFm = 8, kFmRatio = 9, kFold = 10,
    kNoise = 11, kTone = 12, kAmp = 13, kPan = 14,
    kCutA = 15, kResA = 16, kModeA = 17, kGainA = 18, kCutB = 19, kResB = 20, kModeB = 21, kGainB = 22, kLMix = 23,
    kDly = 24, kRev = 25, kDrive = 26,
    kPFreq = 27, kPOrder = 28, kPTeeth = 29, kPRoll = 30, kPRatio = 31, kPAmt = 32, kPFold = 33, kPLevel = 34, kPWidth = 35, kPFm = 36, kPSkew = 37,
    kOFreq = 38, kOLevel = 39, kOPart = 40, kOTilt = 41, kOTens = 42, kODens = 43, kOWarp = 44, kOPeak = 45, kOFund = 46, kOWidth = 47, kOSpread = 48,
    kFLevel = 49, kFRate = 50, kFPos = 51, kFSize = 52, kReson = 53,
    kX = 54, kY = 55, kZ = 56, kSpSpread = 57, kSpAir = 58;      // (space: ObliqSonic only)
var kn = 60;
var ctl = { |kb, i, lagTime| var v = In.kr(kb + i); if (lagTime.isNil) { Lag.kr(v, lag) } { if (lagTime > 0) { Lag.kr(v, lagTime) } { v } } };

// ---------------------------------------------------------------- oscillator stack, one def per waveform
// wave: 1 triangle, 2 square/pulse, 3 saw, 4 sine
4.do { |w|
    SynthDef(("ovOsc" ++ (w + 1)).asSymbol, { |kb = 0, vbus = 16, uni = 3, natbus = 14|
        var freq = ctl.(kb, kFreq, 0), pw = ctl.(kb, kPw), det = ctl.(kb, kDetune), drift = ctl.(kb, kDrift);
        var spread = ctl.(kb, kSpread), level = ctl.(kb, kVco), sub = ctl.(kb, kSub), sub2 = In.kr(kb + kSub2);
        var fm = ctl.(kb, kFm), fmRatio = In.kr(kb + kFmRatio), fold = ctl.(kb, kFold), noise = ctl.(kb, kNoise), tone = ctl.(kb, kTone);
        var reson = ctl.(kb, kReson);
        var offs = [0, -1, 1, -0.55, 0.55, -0.25, 0.25];
        var sigL = 0, sigR = 0, main, n, fmSig, f, wide, st, nat;
        7.do { |i|
            var on = (uni > i).lag(0.01);
            var fr = freq * (offs[i] * det * 0.5 + (LFNoise1.kr(0.3 + (i * 0.11)) * drift * 0.18)).midiratio;
            var o = switch(w,
                0, { LFTri.ar(fr, Rand(0, 4)) },
                1, { Pulse.ar(fr, pw.clip(0.02, 0.98)) },
                2, { Saw.ar(fr) },
                3, { SinOsc.ar(fr, Rand(0, 2pi)) });
            var p = if (i == 0) { 0 } { if (i.odd) { -1 } { 1 } * spread * (0.4 + (i * 0.1)) };
            sigL = sigL + (o * on * (1 - p).clip(0, 2) * 0.5);
            sigR = sigR + (o * on * (1 + p).clip(0, 2) * 0.5);
        };
        st = [sigL, sigR] / uni.max(1).sqrt;
        st = (st * level * 0.35).tanh;
        // sub: square one (or two) octaves down
        st = st + (Pulse.ar(freq * Select.kr(sub2 > 0.5, [0.5, 0.25]), 0.5) * sub * 0.4);
        // FM pair: sine carrier, index swept by the amount
        fmSig = SinOsc.ar(freq, SinOsc.ar(freq * fmRatio) * fm * 6);
        st = st + (fmSig * fm * 0.5);
        // wavefolder
        st = SelectX.ar(fold, [st, (st * (1 + (fold * 6))).fold2(1) * 0.8]);
        // noise, coloured by TONE
        n = LPF.ar(WhiteNoise.ar ! 2, tone.clip(40, 16000));
        st = st + (n * noise * 0.6);
        // nature resonator: the nature scene rings at the note's pitch
        nat = CombL.ar(In.ar(natbus, 2) * 3, 0.06, (1 / freq.max(20)).clip(0.0005, 0.06), 0.9) * reson;
        st = st + nat;
        Out.ar(vbus, st);
    }).writeDefFile(out);
};

// ---------------------------------------------------------------- polygonal oscillator
SynthDef(\ovPoly, { |kb = 0, vbus = 16, cycle = 0|
    var f = ctl.(kb, kPFreq, 0), main = In.ar(vbus, 1);
    var freq = f * (1 + (ctl.(kb, kPFm) * main * 3));
    var xy = OblqPoly.ar(freq, ctl.(kb, kPOrder, 0), ctl.(kb, kPTeeth, 0), ctl.(kb, kPRoll, 0), In.kr(kb + kPRatio), ctl.(kb, kPAmt), cycle, ctl.(kb, kPSkew));
    var fold = ctl.(kb, kPFold), w = ctl.(kb, kPWidth), level = ctl.(kb, kPLevel);
    xy = SelectX.ar(fold, [xy, (xy * (1 + (fold * 6))).sin]);
    Out.ar(vbus, [(xy[0] * (1 + w) * 0.5) + (xy[1] * (1 - w) * 0.5), (xy[1] * (1 + w) * 0.5) + (xy[0] * (1 - w) * 0.5)] * level * 0.9);
    // the plug-in's XY screen reads these two
    Out.kr(kb + kn - 2, A2K.kr(xy[0])); Out.kr(kb + kn - 1, A2K.kr(xy[1]));
}).writeDefFile(out);

// ---------------------------------------------------------------- additive bank: 1, 3 or 5 chord voices
[1, 3, 5].do { |nv|
    SynthDef(("ovOde" ++ nv).asSymbol, { |kb = 0, vbus = 16, bank = 0, factor = 0, gates = 255, fundSq = 0,
            c0 = 0, c1 = 0, c2 = 0, c3 = 0, c4 = 0|
        var f = ctl.(kb, kOFreq, 0), level = ctl.(kb, kOLevel), spread = ctl.(kb, kOSpread), w = ctl.(kb, kOWidth), fund = ctl.(kb, kOFund);
        var semis = [c0, c1, c2, c3, c4], dets = [0, -1, 1, -2, 2];
        var part = In.kr(kb + kOPart).min(if (nv == 5) { 64 } { 128 });
        var a = 0, b = 0, sig, fu;
        nv.do { |i|
            var ab = OblqAdd.ar(f * (semis[i] + (spread * dets[i] * 0.35)).midiratio, part, In.kr(kb + kOTilt), In.kr(kb + kOTens),
                In.kr(kb + kODens), In.kr(kb + kOWarp), In.kr(kb + kOPeak), bank, factor, gates);
            a = a + ab[0]; b = b + ab[1];
        };
        a = a * 0.75 / nv.sqrt; b = b * 0.75 / nv.sqrt;
        fu = Select.ar(fundSq > 0.5, [SinOsc.ar(f) * 0.8, Pulse.ar(f) * 0.6]) * fund;
        a = a + fu; b = b + fu;
        sig = [(a * (1 + w) * 0.5) + (b * (1 - w) * 0.5), (b * (1 + w) * 0.5) + (a * (1 - w) * 0.5)];
        Out.ar(vbus, sig * level);
    }).writeDefFile(out);
};

// ---------------------------------------------------------------- the field recording, played from the keys
// two overlapping loop readers half a loop apart, each faded at its ends: a seamless micro-loop of any size
SynthDef(\ovField, { |kb = 0, vbus = 16, buf = 0, scatter = 0|
    var level = ctl.(kb, kFLevel), rate = ctl.(kb, kFRate, 0.02), pos = ctl.(kb, kFPos, 0.05), size = ctl.(kb, kFSize, 0.05);
    var frames = BufFrames.kr(buf), dur = BufDur.kr(buf);
    var start = (pos + scatter).clip(0, 0.97) * frames;
    var len = (size.clip(0.003, 1) * frames).min(frames - start).max(64);
    var ph = Phasor.ar(0, rate * BufRateScale.kr(buf) / len, 0, 1);
    var sig = 2.collect { |i|
        var p = (ph + (i * 0.5)).wrap(0, 1);
        BufRd.ar(2, buf, start + (p * len), 1, 4) * (p * pi).sin.squared
    }.sum;
    Out.ar(vbus, sig * level);
}).writeDefFile(out);

// ---------------------------------------------------------------- filter, amp, drive, sends: one def per link mode
// link: 1 off (A left / B right of the mix knob), 2 A controls B, 3 series, 4 four-pole, 5 stereo (A left ear, B right ear)
5.do { |li|
    var link = li + 1;
    SynthDef(("ovFilt" ++ link).asSymbol, { |kb = 0, vbus = 16, mix = 0, dly = 2, rev = 4, sonic = 0, amb = 32, pt = 0|
        var in = In.ar(vbus, 2);
        var cA = ctl.(kb, kCutA, 0), rA = ctl.(kb, kResA), mA = ctl.(kb, kModeA), gA = ctl.(kb, kGainA);
        var cB = ctl.(kb, kCutB, 0), rB = ctl.(kb, kResB), mB = ctl.(kb, kModeB), gB = ctl.(kb, kGainB);
        var lmix = ctl.(kb, kLMix), amp = In.kr(kb + kAmp), pan = ctl.(kb, kPan, 0.01), drive = ctl.(kb, kDrive, 0.02);
        var a, b, sig, dg, dc;
        sig = switch(link,
            5, { [OblqFilter.ar(in[0], cA, rA, mA, gA), OblqFilter.ar(in[1], cB, rB, mB, gB)] },
            3, { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(a, cB, rB, mB, gB); XFade2.ar(a, b, lmix * 2 - 1) },
            4, { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(a, cA, rA, mA, gA); XFade2.ar(a, b, lmix * 2 - 1) },
            { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(in, cB, rB, mB, gB); XFade2.ar(a, b, lmix * 2 - 1) });
        // amp: the envelope arrives once per block, so ramp it across the block
        sig = sig * Lag.kr(amp, 0.0015).max(0) * 0.26;
        // DRIVE saturates each voice on its own, so chords stay clean
        dg = 1 + (drive * 7); dc = 1 / (1 + (drive * 2.5));
        sig = (sig * dg).tanh * dc;
        sig = [sig[0] * (1 - pan).sqrt, sig[1] * pan.sqrt] * 1.414;
        Out.ar(dly, sig * ctl.(kb, kDly));
        Out.ar(rev, sig * ctl.(kb, kRev));
        Out.ar(mix, sig);
    }).writeDefFile(out);
};

// ---------------------------------------------------------------- the same, as a point in space (ObliqSonic)
5.do { |li|
    var link = li + 1;
    SynthDef(("ovFiltS" ++ link).asSymbol, { |kb = 0, vbus = 16, amb = 32, dly = 2, rev = 4|
        var in = In.ar(vbus, 2);
        var cA = ctl.(kb, kCutA, 0), rA = ctl.(kb, kResA), mA = ctl.(kb, kModeA), gA = ctl.(kb, kGainA);
        var cB = ctl.(kb, kCutB, 0), rB = ctl.(kb, kResB), mB = ctl.(kb, kModeB), gB = ctl.(kb, kGainB);
        var lmix = ctl.(kb, kLMix), amp = In.kr(kb + kAmp), drive = ctl.(kb, kDrive, 0.02);
        var a, b, sig, dg, dc, mono;
        sig = switch(link,
            5, { [OblqFilter.ar(in[0], cA, rA, mA, gA), OblqFilter.ar(in[1], cB, rB, mB, gB)] },
            3, { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(a, cB, rB, mB, gB); XFade2.ar(a, b, lmix * 2 - 1) },
            4, { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(a, cA, rA, mA, gA); XFade2.ar(a, b, lmix * 2 - 1) },
            { a = OblqFilter.ar(in, cA, rA, mA, gA); b = OblqFilter.ar(in, cB, rB, mB, gB); XFade2.ar(a, b, lmix * 2 - 1) });
        sig = sig * Lag.kr(amp, 0.0015).max(0) * 0.26;
        dg = 1 + (drive * 7); dc = 1 / (1 + (drive * 2.5));
        sig = (sig * dg).tanh * dc;
        Out.ar(dly, sig * ctl.(kb, kDly));
        Out.ar(rev, sig * ctl.(kb, kRev));
        mono = (sig[0] + sig[1]) * 0.7071;
        Out.ar(amb, OblqEncode.ar(mono, In.kr(kb + kX), In.kr(kb + kY), In.kr(kb + kZ), In.kr(kb + kSpSpread), In.kr(kb + kSpAir), \dopp.kr(0.5), \ref.kr(2)));
    }).writeDefFile(out);
};

// ---------------------------------------------------------------- nature scenes (synthesised, never the same twice)
// each writes a stereo scene to `natbus`; level is applied by the master
SynthDef(\oNat1, { |natbus = 14|        // wind
    var n = PinkNoise.ar ! 2, c = LFNoise1.kr(0.08).range(220, 900), g = LFNoise1.kr([0.12, 0.1]).range(0.15, 1), wh = LFNoise1.kr(0.05).range(0, 1);
    var body = BPF.ar(n, [c, c * 1.12], 0.7), whistle = BPF.ar(n, c * [2.6, 2.9], 35 / (c * 2.7)) * wh.squared * 6;
    Out.ar(natbus, (body * 1.6 + whistle) * g * 0.5);
}).writeDefFile(out);
SynthDef(\oNat2, { |natbus = 14|        // birds
    var chirp = { |rate, lo, hi|
        var t = Dust.kr(rate), f = TRand.kr(lo, hi, t), syl = TIRand.kr(2, 7, t);
        var e = EnvGen.kr(Env.perc(0.005, 0.5), t) * LFPulse.kr(syl * 4, 0, 0.5).lag(0.01);
        var sw = EnvGen.kr(Env([1, 1.25, 0.9], [0.08, 0.3]), t);
        Pan2.ar(SinOsc.ar(f * sw * (1 + (SinOsc.kr(TRand.kr(18, 40, t)) * 0.04))) * e * 0.12, TRand.kr(-0.9, 0.9, t))
    };
    var bed = BPF.ar(PinkNoise.ar ! 2, 3000, 1.5) * 0.02;
    Out.ar(natbus, chirp.(0.9, 2200, 4800) + chirp.(0.6, 1600, 3200) + chirp.(0.4, 3500, 6000) + bed);
}).writeDefFile(out);
SynthDef(\oNat3, { |natbus = 14|        // beach
    var swell = (SinOsc.kr([0.11, 0.093], [0, 1.3]).range(0, 1) ** 2.2).lag(0.3);
    var n = PinkNoise.ar ! 2 + (WhiteNoise.ar ! 2 * 0.3);
    var surf = LPF.ar(n, swell.linexp(0, 1, 500, 7000)) * (0.08 + (swell * 0.9));
    var hiss = HPF.ar(WhiteNoise.ar ! 2, 5000) * swell.squared * 0.15;
    Out.ar(natbus, (surf + hiss) * 0.5);
}).writeDefFile(out);
SynthDef(\oNat4, { |natbus = 14|        // geyser
    var t = Dust.kr(0.12), e = EnvGen.kr(Env([0, 1, 0.6, 0], [0.4, 2.5, 3], [2, 0, -3]), t);
    var bub = (BPF.ar(Dust2.ar(LFNoise1.kr(0.3).range(20, 90) ! 2), LFNoise1.kr(2).range(250, 700), 0.15) * 3);
    var jet = HPF.ar(WhiteNoise.ar ! 2, 1800 - (e * 900)) * e * 0.5;
    var rumble = LPF.ar(BrownNoise.ar ! 2, 120) * (0.25 + (e * 0.6));
    Out.ar(natbus, (bub * 0.5 + jet + rumble) * 0.6);
}).writeDefFile(out);
SynthDef(\oNat5, { |natbus = 14|        // forest
    var leaves = BPF.ar(PinkNoise.ar ! 2, LFNoise1.kr(0.1).range(1500, 4000), 1.2) * LFNoise1.kr([0.2, 0.17]).range(0.03, 0.2);
    var t = Dust.kr(0.35), f = TRand.kr(1800, 3600, t);
    var bird = Pan2.ar(SinOsc.ar(f * EnvGen.kr(Env([1, 1.3, 1], [0.05, 0.15]), t)) * EnvGen.kr(Env.perc(0.01, 0.25), t) * 0.1, TRand.kr(-1, 1, t));
    var tk = Dust.kr(0.25), knock = Pan2.ar(BPF.ar(Decay2.ar(Impulse.ar(LFPulse.kr(0.25, 0, 0.12) * TRand.kr(11, 16, tk)), 0.001, 0.02), 1300, 0.2) * 1.5, -0.4);
    Out.ar(natbus, leaves + bird + knock);
}).writeDefFile(out);
SynthDef(\oNat6, { |natbus = 14|        // water (stream)
    var d = { BPF.ar(Dust2.ar(LFNoise1.kr(0.5).range(300, 900)), LFNoise1.kr(8).exprange(500, 4500), 0.08) * 6 } ! 2;
    var bed = BPF.ar(PinkNoise.ar ! 2, [900, 1100], 1.4) * 0.12;
    Out.ar(natbus, (d + bed) * 0.5);
}).writeDefFile(out);
SynthDef(\oNat7, { |natbus = 14|        // thunder and rain
    var rain = (HPF.ar(PinkNoise.ar ! 2, 700) * 0.14) + (BPF.ar(Dust2.ar(900 ! 2), 5000, 0.6) * 0.5);
    var t = Dust.kr(0.07), e = EnvGen.kr(Env([0, 1, 0.3, 0.5, 0], [0.02, 0.6, 1.2, 5], -3), t);
    var boom = LPF.ar(BrownNoise.ar ! 2 + (Dust2.ar(30 ! 2) * 2), TRand.kr(60, 240, t) * (0.6 + e)) * e * 2.2;
    Out.ar(natbus, rain + Balance2.ar(boom[0], boom[1], TRand.kr(-0.7, 0.7, t)));
}).writeDefFile(out);
SynthDef(\oNat8, { |natbus = 14|        // night (crickets, far frogs)
    var cr = { |f, r, p| Pan2.ar(SinOsc.ar(f) * LFPulse.kr(r, 0, 0.5).lag(0.002) * LFPulse.kr(LFNoise0.kr(0.3).range(0.4, 1.1), 0, 0.6).lag(0.02) * 0.035, p) };
    var frog = Pan2.ar(BPF.ar(Saw.ar(LFNoise0.kr(0.4).range(160, 230)), 900, 0.3) * LFPulse.kr(LFNoise0.kr(0.2).range(1.5, 4), 0, 0.3).lag(0.01) * LFNoise1.kr(0.1).range(0, 0.25), 0.5);
    var air = BPF.ar(PinkNoise.ar ! 2, 6000, 2) * 0.012;
    Out.ar(natbus, cr.(4300, 31, -0.6) + cr.(4700, 27, 0.5) + cr.(3900, 35, 0.1) + frog + air);
}).writeDefFile(out);

// ---------------------------------------------------------------- the field recording as an ambient bed
// a loop window whose start and end are always slowly sliding; two readers crossfade so it never clicks
SynthDef(\oBed, { |fieldbus = 12, buf = 0, rate = 1, rev = 0, gain = 1, norm = 1, drift = 0.1|
    var frames = BufFrames.kr(buf);
    var a = LFNoise2.kr(drift).range(0, 1), b = LFNoise2.kr(drift * 1.13).range(0, 1);
    var start = a * 0.5 * frames, len = ((0.3 + (b * 0.5)) * frames).min(frames - start).max(2048);
    var dir = Select.kr(rev > 0.5, [1, -1]);
    var ph = Phasor.ar(0, dir * rate * BufRateScale.kr(buf) / len, 0, 1);
    var sig = 2.collect { |i|
        var p = (ph + (i * 0.5)).wrap(0, 1);
        BufRd.ar(2, buf, start + (p * len), 1, 4) * (p * pi).sin.squared
    }.sum;
    Out.ar(fieldbus, sig * Lag.kr(gain, 0.05) * norm);
}).writeDefFile(out);

// ---------------------------------------------------------------- one moving copy of the recording (ObliqSonic: six of these)
SynthDef(\oBedS, { |amb = 32, buf = 0, rate = 1, rev = 0, gain = 1, norm = 1, drift = 0.1, kpos = 0, spread = 0.15, air = 0.4, dopp = 0.5, ref = 2, ch = 0|
    var frames = BufFrames.kr(buf);
    var a = LFNoise2.kr(drift * Rand(0.7, 1.4)).range(0, 1), b = LFNoise2.kr(drift * Rand(0.7, 1.4)).range(0, 1);
    var start = a * 0.7 * frames, len = ((0.12 + (b * 0.6)) * frames).min(frames - start).max(2048);
    var dir = Select.kr(rev > 0.5, [1, -1]);
    var ph = Phasor.ar(0, dir * rate * BufRateScale.kr(buf) / len, Rand(0, 1), 1);
    var sig = 2.collect { |i|
        var p = (ph + (i * 0.5)).wrap(0, 1);
        Select.ar(ch, BufRd.ar(2, buf, start + (p * len), 1, 4)) * (p * pi).sin.squared
    }.sum;
    var xyz = In.kr(kpos, 3);
    Out.ar(amb, OblqEncode.ar(sig * Lag.kr(gain, 0.05) * norm * 0.62, xyz[0], xyz[1], xyz[2], spread, air, dopp, ref));
}).writeDefFile(out);

// ---------------------------------------------------------------- master: chorus > ping-pong delay > reverb > limiter > 16 bit
// control block (gb): 0 chorus 1 dlyMix 2 dlyTime(s) 3 dlyFb 4 reverb 5 space 6 volume 7 natLevel 8 fieldLevel
// it writes meters back: gb+16 follower (sampler), +17 output env, +18/+19 VU L/R, +20 nature env
SynthDef(\oFx, { |gb = 0, mix = 0, dly = 2, rev = 4, fieldbus = 12, natbus = 14, outbus = 0|
    var g = { |i, l = 0.02| Lag.kr(In.kr(gb + i), l) };
    var dry = In.ar(mix, 2), dsend = In.ar(dly, 2), rsend = In.ar(rev, 2);
    var nat = In.ar(natbus, 2) * g.(7, 0.05), field = In.ar(fieldbus, 2) * g.(8, 0.05);
    var ch = g.(0), sig, c, tapL, tapR, fb, dt, rv, sp, wet, lim, pk, foll;
    // chorus / ensemble
    c = [DelayC.ar(dry[0], 0.05, (0.011 + (SinOsc.kr(0.31) * (0.002 + (ch * 0.005)))).max(0.001)),
         DelayC.ar(dry[1], 0.05, (0.013 + (SinOsc.kr(0.47, 2) * (0.002 + (ch * 0.005)))).max(0.001))];
    sig = (dry * (1 - (ch * 0.45))) + (c * 0.7 * ch) + ([1, -1] * DelayC.ar(dry.sum * 0.5, 0.05, (0.017 + (SinOsc.kr(0.23, 4) * (0.002 + (ch * 0.005)))).max(0.001)) * 0.4 * ch);
    // ping-pong delay with a slightly wobbly, filtered feedback
    dt = (g.(2, 0.2) + (SinOsc.kr(0.6) * 0.0006)).clip(0.01, 2.9);
    fb = LocalIn.ar(2);
    tapL = DelayC.ar(((dsend.sum * 0.5) + (nat.sum * 0.15)) * g.(1) + fb[1], 3, dt);
    tapR = DelayC.ar(fb[0], 3, dt);
    LocalOut.ar([(LPF.ar(tapL, 4200) * g.(3)).tanh, (LPF.ar(tapR, 4200) * g.(3)).tanh]);
    sig = sig + [tapL, tapR];
    // reverb: REVERB = amount, SPACE = size and brightness
    sp = g.(5, 0.05);
    rv = FreeVerb2.ar(rsend[0] + (tapL * 0.5) + (nat[0] * 0.8) + (field[0] * 0.5), rsend[1] + (tapR * 0.5) + (nat[1] * 0.8) + (field[1] * 0.5), 1, 0.55 + (sp * 0.43), 0.75 - (sp * 0.55));
    rv = LPF.ar(rv, 3500 + (sp * 9000));
    wet = g.(4) * 1.7;
    sig = sig + nat + field + (rv * wet);
    sig = LeakDC.ar(sig * g.(6) / 3);
    // transparent look-ahead limiter, then a 16-bit output stage
    sig = Limiter.ar(sig, 0.89, 0.005);
    sig = (sig * 32767 + (WhiteNoise.ar(0.5) * [1, -1])).round(1) / 32767;
    Out.ar(outbus, sig);
    // meters and followers, read by the plug-in from the control buses
    foll = Amplitude.kr((nat + field).sum * 0.5, 0.01, 0.25);
    Out.kr(gb + 16, [foll, Amplitude.kr(sig.sum * 0.5, 0.01, 0.25), Amplitude.kr(sig[0], 0.005, 0.3), Amplitude.kr(sig[1], 0.005, 0.3), Amplitude.kr(nat.sum * 0.5, 0.02, 0.4)]);
}).writeDefFile(out);

// ---------------------------------------------------------------- master for ObliqSonic: the effects and the nature bed are points too
// gb block as above, plus positions: gb+24.. (x y z) for fx L, fx R, nature L, nature R; gb+36 spread, +37 air, +38 doppler, +39 ref
SynthDef(\oFxS, { |gb = 0, amb = 32, dly = 2, rev = 4, natbus = 14, outbus = 0|
    var g = { |i, l = 0.02| Lag.kr(In.kr(gb + i), l) };
    var dsend = In.ar(dly, 2), rsend = In.ar(rev, 2);
    var nat = In.ar(natbus, 2) * g.(7, 0.05);
    var tapL, tapR, fb, dt, rv, sp, wet, fx, enc, w, gain, sig, spread = In.kr(gb + 36), air = In.kr(gb + 37), dopp = In.kr(gb + 38), ref = In.kr(gb + 39);
    var pos = { |i| In.kr(gb + 24 + (i * 3), 3) };
    dt = (g.(2, 0.2) + (SinOsc.kr(0.6) * 0.0006)).clip(0.01, 2.9);
    fb = LocalIn.ar(2);
    tapL = DelayC.ar(((dsend.sum * 0.5) + (nat.sum * 0.15)) * g.(1) + fb[1], 3, dt);
    tapR = DelayC.ar(fb[0], 3, dt);
    LocalOut.ar([(LPF.ar(tapL, 4200) * g.(3)).tanh, (LPF.ar(tapR, 4200) * g.(3)).tanh]);
    sp = g.(5, 0.05);
    rv = FreeVerb2.ar(rsend[0] + (tapL * 0.5) + (nat[0] * 0.8), rsend[1] + (tapR * 0.5) + (nat[1] * 0.8), 1, 0.55 + (sp * 0.43), 0.75 - (sp * 0.55));
    rv = LPF.ar(rv, 3500 + (sp * 9000));
    wet = g.(4) * 1.7;
    fx = [tapL, tapR] + (rv * wet);
    enc = In.ar(amb, 16)
        + OblqEncode.ar(fx[0], pos.(0)[0], pos.(0)[1], pos.(0)[2], 0.55 + (spread * 0.45), air, dopp, ref)
        + OblqEncode.ar(fx[1], pos.(1)[0], pos.(1)[1], pos.(1)[2], 0.55 + (spread * 0.45), air, dopp, ref)
        + OblqEncode.ar(nat[0], pos.(2)[0], pos.(2)[1], pos.(2)[2], 0.35 + (spread * 0.65), air, dopp, ref)
        + OblqEncode.ar(nat[1], pos.(3)[0], pos.(3)[1], pos.(3)[2], 0.35 + (spread * 0.65), air, dopp, ref);
    enc = enc * g.(6) / 3;
    // linked limiter driven by the omni (W) channel keeps the 16 channels in proportion
    w = LeakDC.ar(enc[0]);
    gain = (0.89 / Amplitude.ar(w, 0.001, 0.15).max(0.89));
    sig = enc * gain;
    sig = (sig * 32767 + WhiteNoise.ar(0.5)).round(1) / 32767;
    Out.ar(outbus, sig);
    Out.kr(gb + 16, [Amplitude.kr(nat.sum * 0.5, 0.01, 0.25), Amplitude.kr(sig[0], 0.01, 0.25), Amplitude.kr((sig[0] + sig[1]) * 0.5, 0.005, 0.3), Amplitude.kr((sig[0] - sig[1]) * 0.5, 0.005, 0.3), Amplitude.kr(nat.sum * 0.5, 0.02, 0.4)]);
}).writeDefFile(out);

"oblq defs written".postln;
0.exit;
)
