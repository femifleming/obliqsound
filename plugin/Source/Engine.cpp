#include "Engine.h"
#include <cmath>

using juce::jlimit; using juce::jmax; using juce::jmin;

namespace
{
    // a voice's control block (keep in step with sc/defs/oblq.scd)
    enum VB { kFreq, kPw, kDetune, kDrift, kSpread, kVco, kSub, kSub2, kFm, kFmRatio, kFold, kNoise, kTone, kAmp, kPan,
              kCutA, kResA, kModeA, kGainA, kCutB, kResB, kModeB, kGainB, kLMix, kDly, kRev, kDrive,
              kPFreq, kPOrder, kPTeeth, kPRoll, kPRatio, kPAmt, kPFold, kPLevel, kPWidth, kPFm, kPSkew,
              kOFreq, kOLevel, kOPart, kOTilt, kOTens, kODens, kOWarp, kOPeak, kOFund, kOWidth, kOSpread,
              kFLevel, kFRate, kFPos, kFSize, kReson, kX, kY, kZ, kSpSpread, kSpAir };
    inline float mtof (float m) { return 440.0f * std::pow (2.0f, (m - 69.0f) / 12.0f); }
    inline float semi (float s) { return std::pow (2.0f, s / 12.0f); }
    const float kChords[12][5] = { { 0, 0, 0, 0, 0 }, { 0, -12, 12, -24, 24 }, { 0, -5, 7, -12, 19 }, { 0, 5, 7, 12, 17 }, { 0, 4, 7, 12, 16 }, { 0, 3, 7, 12, 15 },
                                   { 0, 4, 7, 11, 14 }, { 0, 3, 7, 10, 14 }, { 0, 7, 14, 16, 19 }, { 0, 5, 10, 15, 20 }, { 0, 1, 2, -1, -2 }, { 0, 2, 4, 6, 8 } };
    const float kDlyBeats[9] = { 0.125f, 0.1666667f, 0.25f, 0.3333333f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f };
    const float kSyncDivs[11] = { 16, 8, 4, 2, 1, 0.6666667f, 0.5f, 0.3333333f, 0.25f, 0.1666667f, 0.125f };
}

// every parameter the engine reads, resolved to an index once
struct Engine::Ids
{
    int VCO, Tune1, pw, waveform, detune, vib, OctDn, OctUp, LPFreq, Res, aMode, aGain, mod, FAtt, FDec, FSus, FRel,
        AmpSamp, fVoice, ampVCO, noise, pLevel, oLevel, bDepth, lDepth, fPitch, fPos, fSize, fKey, bCut, bRes, bMode, bGain, VCAinit,
        AAtt, ADec, ASus, ARel, chorus, tone, space, reverb, volume, drive, fScatter, fSpeed, glide, fRev,
        pTune, pOrder, pTeeth, pRoll, pRatio, pAmt, pFM, pWidth, pFold, pPhase, pSlew, pSpin, pCycle, pRegular, pSnap,
        oPart, oBank, oFactor, oTension, oTilt, oFund, oWidth, oChord, oTune, oDens, oFine, oWarp, oSpread, oPeak, oVoices, oFundWave,
        link, lMix, lRnd, l1Sync, l2Sync, uniLock, sub2, l1Rate, l2Rate, l1Shape, l2Shape, uni, pEnv, sub, drift, meAtt, meDec, spread, fm, fmRatio,
        fAtt, fRel, fold, fGain, vStereo, dlyMix, resonate, dlyTime, velAmt, dlyFb, bendRange,
        bSpeed, bCoh, bSep, bAli, lRate, lSigma, lRho, lBeta, scBoidV, rndAll,
        spMode, spSpeed, spDist, spHeight, spDev, spRot, spSpread, spDopp, spAir, spGrav, spCoh, spFSplay;
};

Engine::Engine (ParamStore& p, bool isSonic, const juce::var& layout) : params (p), sonic (isSonic)
{
    id = std::make_unique<Ids>();
   #define I(n) id->n = params.find (#n)
    I(VCO); I(Tune1); I(pw); I(waveform); I(detune); I(vib); I(OctDn); I(OctUp); I(LPFreq); I(Res); I(aMode); I(aGain); I(mod); I(FAtt); I(FDec); I(FSus); I(FRel);
    I(AmpSamp); I(fVoice); I(ampVCO); I(noise); I(pLevel); I(oLevel); I(bDepth); I(lDepth); I(fPitch); I(fPos); I(fSize); I(fKey); I(bCut); I(bRes); I(bMode); I(bGain); I(VCAinit);
    I(AAtt); I(ADec); I(ASus); I(ARel); I(chorus); I(tone); I(space); I(reverb); I(volume); I(drive); I(fScatter); I(fSpeed); I(glide); I(fRev);
    I(pTune); I(pOrder); I(pTeeth); I(pRoll); I(pRatio); I(pAmt); I(pFM); I(pWidth); I(pFold); I(pPhase); I(pSlew); I(pSpin); I(pCycle); I(pRegular); I(pSnap);
    I(oPart); I(oBank); I(oFactor); I(oTension); I(oTilt); I(oFund); I(oWidth); I(oChord); I(oTune); I(oDens); I(oFine); I(oWarp); I(oSpread); I(oPeak); I(oVoices); I(oFundWave);
    I(link); I(lMix); I(lRnd); I(l1Sync); I(l2Sync); I(uniLock); I(sub2); I(l1Rate); I(l2Rate); I(l1Shape); I(l2Shape); I(uni); I(pEnv); I(sub); I(drift); I(meAtt); I(meDec); I(spread); I(fm); I(fmRatio);
    I(fAtt); I(fRel); I(fold); I(fGain); I(vStereo); I(dlyMix); I(resonate); I(dlyTime); I(velAmt); I(dlyFb); I(bendRange);
    I(bSpeed); I(bCoh); I(bSep); I(bAli); I(lRate); I(lSigma); I(lRho); I(lBeta); I(scBoidV); I(rndAll);
    I(spMode); I(spSpeed); I(spDist); I(spHeight); I(spDev); I(spRot); I(spSpread); I(spDopp); I(spAir); I(spGrav); I(spCoh); I(spFSplay);
   #undef I
    for (int i = 1; i <= 26; ++i) sIds.push_back (params.find ("S" + juce::String (i)));
    for (int i = 1; i <= 6; ++i) { jSrc.push_back (params.find ("j" + juce::String (i) + "Src")); jAtt.push_back (params.find ("j" + juce::String (i) + "Att")); }
    for (int i = 1; i <= 8; ++i) oG.push_back (params.find ("oG" + juce::String (i)));
    for (auto ab : { "a", "b" }) for (int i = 1; i <= 3; ++i)
    {
        lSrc.push_back (params.find (juce::String (ab) + juce::String (i) + "Src"));
        lDst.push_back (i == 1 ? -1 : params.find (juce::String (ab) + juce::String (i) + "Dst"));
        lAtt.push_back (params.find (juce::String (ab) + juce::String (i) + "Att"));
    }
    for (auto n : { "oExp", "oLin", "oDen", "oWarp" }) { oCvS.push_back (params.find (juce::String (n) + "Src")); oCvA.push_back (params.find (juce::String (n) + "Att")); }
    for (auto n : { "scSource", "scPoly", "scOde", "scFilt", "scFx", "scMot" }) scIds.push_back (params.find (n));
    for (int i = 1; i <= 4; ++i) ccnIds.push_back (params.find ("ccn" + juce::String (i)));

    nDst = layout["destinations"].size() + 1;
    for (int i = 0; i < params.size(); ++i)
    {
        const auto& s = params.def (i).id;
        if (s.startsWithChar ('p') && s.containsChar ('_') && s.substring (1).retainCharacters ("0123456789_") == s.substring (1))
            pinIds.push_back ({ i, s.substring (1).upToFirstOccurrenceOf ("_", false, false).getIntValue() - 1, s.fromFirstOccurrenceOf ("_", false, false).getIntValue() - 1 });
    }
    if (auto* arr = layout["swarm"].getArray())
        for (auto& e : *arr)
        {
            Sw s; s.idx = params.find (e["ch"].toString()); if (s.idx < 0) continue;
            s.sec = (int) e["sec"]; s.boid = (int) e["boid"]; s.axisY = e["axis"].toString() == "Y"; s.sign = (float) (double) e["sign"];
            s.lor = e["lor"].toString() == "X" ? 0 : (e["lor"].toString() == "Y" ? 1 : 2);
            s.mul = (bool) e["mul"]; s.amt = (float) (double) e["amt"]; s.lo = (float) (double) e["lo"]; s.hi = (float) (double) e["hi"];
            swarm.push_back (s);
        }
    if (auto* arr = layout["fnorm"].getArray()) for (auto& v : *arr) fnorm.push_back ((float) (double) v);
    eff.assign ((size_t) params.size(), 0.0f);
    for (int b = 0; b < 8; ++b) { boidX[b] = rnd (-0.8f, 0.8f); boidY[b] = rnd (-0.8f, 0.8f); boidVX[b] = rnd (-0.01f, 0.01f); boidVY[b] = rnd (-0.01f, 0.01f); }
    for (int i = 0; i < kPoints; ++i)
    {
        auto& q = pts[(size_t) i]; const float a = (float) i * 2.39996f;
        q = {};
        q.fx = std::cos (a) * 0.6f; q.fy = std::sin (a) * 0.6f; q.fz = rnd (-0.3f, 0.3f);
        q.vx = rnd (-0.1f, 0.1f); q.vy = rnd (-0.1f, 0.1f); q.vz = rnd (-0.05f, 0.05f);
        q.lx = rnd (-8, 8); q.ly = rnd (-8, 8); q.lz = rnd (18, 32);
        q.gx = std::cos (a) * 0.7f; q.gy = std::sin (a) * 0.7f; q.gz = rnd (-0.2f, 0.2f);
        q.qx = -std::sin (a) * 0.3f; q.qy = std::cos (a) * 0.3f;
        q.ds = rnd (-1, 1); q.dr = rnd (-1, 1);
        q.x = q.tx = q.fx * 3.0f; q.y = q.ty = q.fy * 3.0f;
    }
}

Engine::~Engine() { release(); }

// ------------------------------------------------------------------------------------------------ set-up
bool Engine::prepare (double sampleRate, const juce::File& res)
{
    release();
    sr = sampleRate; dt = 64.0f / (float) sr;
    const int nOut = numOutputs();
    aBase = nOut + 2; aMix = aBase; aDly = aBase + 2; aRev = aBase + 4; aField = aBase + 6; aNat = aBase + 8; aAmb = aBase + 10; aVoice0 = aBase + 26;
    if (! sc.start (sr, nOut, res.getChildFile ("plugins").getFullPathName().toStdString())) { lastError = "The synthesis server could not start."; return false; }
    if (! sc.loadDefs (res.getChildFile ("defs").getFullPathName().toStdString())) { lastError = "The SynthDefs could not be loaded."; sc.stop(); return false; }
    loadSamples (res.getChildFile ("samples"));

    sc.send (OscMsg ("/g_new").i (10).i (0).i (0));                                   // voices, first in the chain
    if (sonic)
    {
        sc.send (OscMsg ("/s_new").s ("oFxS").i (30).i (1).i (0).s ("gb").i (kGb).s ("amb").i (aAmb).s ("dly").i (aDly).s ("rev").i (aRev).s ("natbus").i (aNat));
    }
    else
        sc.send (OscMsg ("/s_new").s ("oFx").i (30).i (1).i (0).s ("gb").i (kGb).s ("mix").i (aMix).s ("dly").i (aDly).s ("rev").i (aRev).s ("fieldbus").i (aField).s ("natbus").i (aNat));
    for (auto& v : voices) v = {};
    for (int i = 0; i < kVoices; ++i) voices[(size_t) i].slot = i;
    samplerSel = -1; natOn = bedOn = false;
    noteCounter = generation = heldCount = 0;
    sc.preBlock = [this] (int done) { hostPos = done; tick(); };
    for (int i = 0; i < params.size(); ++i) eff[(size_t) i] = params.get (i);
    lastRnd = (int) params.get (id->rndAll); lastLRnd = (int) params.get (id->lRnd);
    sc.pump (4);
    return true;
}

void Engine::release() { sc.preBlock = nullptr; sc.stop(); }

void Engine::loadSamples (const juce::File& dir)
{
    juce::AudioFormatManager fm; fm.registerBasicFormats();
    juce::StringArray names; names.addLines (dir.getChildFile ("index.txt").loadFileAsString());
    names.removeEmptyStrings();
    numFiles = 0;
    for (int i = 0; i < names.size(); ++i)
    {
        std::unique_ptr<juce::AudioFormatReader> r (fm.createReaderFor (dir.getChildFile (names[i].trim() + ".wav")));
        if (r == nullptr) { ++numFiles; continue; }
        const int n = (int) r->lengthInSamples;
        juce::AudioBuffer<float> b (2, n); r->read (&b, 0, n, 0, true, true);
        std::vector<float> inter ((size_t) n * 2);
        for (int k = 0; k < n; ++k) { inter[(size_t) k * 2] = b.getSample (0, k); inter[(size_t) k * 2 + 1] = b.getSample (r->numChannels > 1 ? 1 : 0, k); }
        sc.setBuffer (i, 2, n, r->sampleRate, inter.data());
        ++numFiles;
    }
}

// ------------------------------------------------------------------------------------------------ audio
void Engine::process (juce::AudioBuffer<float>& out, const juce::MidiBuffer& midi, double hostBpm)
{
    if (! sc.isRunning()) { out.clear(); return; }
    bpm = hostBpm > 20.0 ? hostBpm : 120.0;
    events.clear(); evPos = 0;
    for (const auto m : midi) events.push_back ({ m.samplePosition, m.getMessage() });
    sc.process (out.getArrayOfWritePointers(), out.getNumChannels(), out.getNumSamples());
    while (evPos < events.size()) handleMidi (events[evPos++].second);        // anything after the last block start
    view.cpu = (float) sc.avgCpu();
}

void Engine::handleMidi (const juce::MidiMessage& m)
{
    if (m.isNoteOn()) noteOn (m.getNoteNumber(), m.getFloatVelocity());
    else if (m.isNoteOff()) noteOff (m.getNoteNumber());
    else if (m.isPitchWheel()) bend = (float) (m.getPitchWheelValue() - 8192) / 8192.0f;
    else if (m.isChannelPressure()) pressure = (float) m.getChannelPressureValue() / 127.0f;
    else if (m.isController())
    {
        cc[(size_t) m.getControllerNumber()] = (float) m.getControllerValue() / 127.0f;
        if (m.getControllerNumber() == 1) wheel = cc[1];
        if (m.getControllerNumber() == 123 || m.getControllerNumber() == 120) allNotesOff();
    }
    else if (m.isAllNotesOff() || m.isAllSoundOff()) allNotesOff();
}

void Engine::allNotesOff()
{
    for (auto& v : voices) if (v.active) { v.held = false; v.drone = false; v.amp.release(); v.filt.release(); }
    heldCount = 0;
}

void Engine::noteOn (int note, float vel)
{
    // retrigger a voice already playing this key, else a free one, else steal the oldest
    Voice* pick = nullptr;
    for (auto& v : voices) if (! v.active) { pick = &v; break; }
    if (pick == nullptr)
    {
        for (auto& v : voices) if (pick == nullptr || v.order < pick->order) pick = &v;
        freeVoice (*pick);
    }
    if (heldCount <= 0) { ++generation; heldCount = 0; }
    ++heldCount;
    startVoice (*pick, note, vel);
}

void Engine::noteOff (int note)
{
    for (auto& v : voices)
        if (v.active && v.held && v.note == note)
        {
            v.held = false; heldCount = jmax (0, heldCount - 1);
            if (! v.drone) { v.amp.release(); v.filt.release(); }
        }
}

void Engine::startVoice (Voice& v, int note, float vel)
{
    const int slot = v.slot;
    v = {};
    v.slot = slot; v.active = true; v.held = true; v.note = note; v.vel = vel; v.order = ++noteCounter; v.gen = generation;
    v.rnd = rnd (-1, 1); v.scat = rnd (-1, 1); v.rx = rnd (-1, 1); v.ry = rnd (-1, 1); v.rz = rnd (-1, 1);
    v.drone = P (id->VCAinit) > 0.001f;
    v.amp.a = jmax (P (id->AAtt), 0.002f); v.amp.d = jmax (P (id->ADec), 0.005f); v.amp.s = P (id->ASus); v.amp.r = jmax (P (id->ARel), 0.01f);
    v.filt.a = jmax (P (id->FAtt), 0.002f); v.filt.d = jmax (P (id->FDec), 0.005f); v.filt.s = P (id->FSus); v.filt.r = jmax (P (id->FRel), 0.01f);
    v.amp.start(); v.filt.start();
    v.meA = jmax (P (id->meAtt), 0.001f); v.meD = jmax (P (id->meDec), 0.01f);
    const float half = P (id->glide) * 0.4f;
    v.glide = half > 0.001f ? lastPitch : (float) note;
    v.glideCoef = half > 0.001f ? 1.0f - std::exp (-dt * 0.6931f / half) : 1.0f;
    lastPitch = (float) note;
    v.order_s = P (id->pOrder); v.teeth_s = P (id->pTeeth);
    v.alive = 1.0f; v.fade = 1.0f;

    const int kb = kKb0 + slot * kKn, vbus = aVoice0 + slot * 2;
    v.group = nextGroup; nextGroup += 8; if (nextGroup > 2000000000) nextGroup = 1000;
    updateVoice (v, 0.0f);                                           // the block of buses is valid before the synths read it
    sc.send (OscMsg ("/g_new").i (v.group).i (1).i (10));
    const int wave = jlimit (1, 4, (int) std::lrint (P (id->waveform)));
    const int uni = jlimit (1, 7, (int) std::lrint (P (id->uni)));
    sc.send (OscMsg ("/s_new").s (("ovOsc" + std::to_string (wave)).c_str()).i (v.group + 1).i (1).i (v.group)
                 .s ("kb").i (kb).s ("vbus").i (vbus).s ("uni").i (uni).s ("natbus").i (aNat));
    v.hasPoly = P (id->pLevel) > 0.0005f;
    if (v.hasPoly)
        sc.send (OscMsg ("/s_new").s ("ovPoly").i (v.group + 2).i (1).i (v.group).s ("kb").i (kb).s ("vbus").i (vbus).s ("cycle").f (P (id->pCycle)));
    v.hasOde = P (id->oLevel) > 0.0005f;
    if (v.hasOde)
    {
        const int ov = (int) std::lrint (P (id->oVoices)); const int nv = ov >= 3 ? 5 : (ov >= 2 ? 3 : 1);
        const int chord = jlimit (0, 11, (int) std::lrint (P (id->oChord)) - 1);
        int gates = 0; for (int g = 0; g < 8; ++g) if (P (oG[(size_t) g]) > 0.5f) gates |= 1 << g;
        sc.send (OscMsg ("/s_new").s (("ovOde" + std::to_string (nv)).c_str()).i (v.group + 3).i (1).i (v.group)
                     .s ("kb").i (kb).s ("vbus").i (vbus).s ("bank").f (std::round (P (id->oBank))).s ("factor").f (std::round (P (id->oFactor)))
                     .s ("gates").i (gates).s ("fundSq").f (P (id->oFundWave) > 1.5f ? 1.0f : 0.0f)
                     .s ("c0").f (kChords[chord][0]).s ("c1").f (kChords[chord][1]).s ("c2").f (kChords[chord][2]).s ("c3").f (kChords[chord][3]).s ("c4").f (kChords[chord][4]));
    }
    v.hasField = P (id->fVoice) > 0.0005f && samplerSel > 8 && numFiles > 0;
    if (v.hasField)
        sc.send (OscMsg ("/s_new").s ("ovField").i (v.group + 4).i (1).i (v.group).s ("kb").i (kb).s ("vbus").i (vbus).s ("buf").i (samplerSel - 9));
    const int link = jlimit (1, 5, (int) std::lrint (P (id->link)));
    if (sonic)
        sc.send (OscMsg ("/s_new").s (("ovFiltS" + std::to_string (link)).c_str()).i (v.group + 5).i (1).i (v.group)
                     .s ("kb").i (kb).s ("vbus").i (vbus).s ("amb").i (aAmb).s ("dly").i (aDly).s ("rev").i (aRev)
                     .s ("dopp").f (P (id->spDopp)).s ("ref").f (1.0f + (P (id->spDist) - 1.0f) * 0.5f));
    else
        sc.send (OscMsg ("/s_new").s (("ovFilt" + std::to_string (link)).c_str()).i (v.group + 5).i (1).i (v.group)
                     .s ("kb").i (kb).s ("vbus").i (vbus).s ("mix").i (aMix).s ("dly").i (aDly).s ("rev").i (aRev));
}

void Engine::freeVoice (Voice& v)
{
    if (v.active) sc.send (OscMsg ("/n_free").i (v.group));
    v.active = false;
}

// ------------------------------------------------------------------------------------------------ one block
void Engine::tick()
{
    while (evPos < events.size() && events[evPos].first <= hostPos + 63) handleMidi (events[evPos++].second);

    // parameters, with the swarm moving the timbre
    const int n = params.size();
    for (int i = 0; i < n; ++i) eff[(size_t) i] = params.get (i);
    updateGlobals (dt);
    {
        float swB[6], swL[6];
        const float bd = eff[(size_t) id->bDepth], ld = eff[(size_t) id->lDepth];
        for (int s = 0; s < 6; ++s) { const float on = params.get (scIds[(size_t) s]); swB[s] = bd * on; swL[s] = ld * on; }
        const float lor[3] = { lorX, lorY, lorZ };
        for (const auto& s : swarm)
        {
            const float m = swB[s.sec] * (s.axisY ? boidY[s.boid] : boidX[s.boid]) + swL[s.sec] * s.sign * lor[s.lor];
            float& v = eff[(size_t) s.idx];
            v = jlimit (s.lo, s.hi, s.mul ? v * std::pow (2.0f, m * 3.0f) : v + m * s.amt);
        }
    }
    if (++pinCounter >= 16 || lastChange < 0) { pinCounter = 0; if (lastChange != params.changeCount.load()) { lastChange = params.changeCount.load(); rebuildPins(); } }
    // RANDOMIZE buttons (edge)
    if ((int) params.get (id->rndAll) != lastRnd) { lastRnd = (int) params.get (id->rndAll); randomize(); }

    updateSampler();
    if (sonic) updateSpace (dt);

    int active = 0;
    for (auto& v : voices)
        if (v.active)
        {
            updateVoice (v, dt);
            if (v.ended > 2) freeVoice (v); else ++active;
        }
    view.voices = active;

    // master block
    float g[40] = {};
    const float samp = eff[(size_t) id->AmpSamp];
    g[0] = eff[(size_t) id->chorus];
    g[1] = eff[(size_t) id->dlyMix];
    g[2] = jlimit (0.01f, 2.9f, kDlyBeats[jlimit (0, 8, (int) std::lrint (eff[(size_t) id->dlyTime]) - 1)] * 60.0f / (float) bpm);
    g[3] = eff[(size_t) id->dlyFb];
    g[4] = eff[(size_t) id->reverb];
    g[5] = eff[(size_t) id->space];
    g[6] = eff[(size_t) id->volume];
    g[7] = samplerSel <= 8 ? 2.6f * (1.0f - std::exp (-samp * 160.0f / 2.6f)) : 0.0f;
    g[8] = 1.0f;
    sc.setControls (kGb, g, 9);
    if (sonic)
    {
        float s[16];
        for (int k = 0; k < 4; ++k) { s[k * 3] = pts[(size_t) (18 + k)].x; s[k * 3 + 1] = pts[(size_t) (18 + k)].y; s[k * 3 + 2] = pts[(size_t) (18 + k)].z; }
        s[12] = eff[(size_t) id->spSpread]; s[13] = eff[(size_t) id->spAir]; s[14] = eff[(size_t) id->spDopp]; s[15] = 1.0f + (eff[(size_t) id->spDist] - 1.0f) * 0.5f;
        sc.setControls (kGb + 24, s, 16);
        for (int k = 0; k < 6; ++k) { const float q[3] = { pts[(size_t) (12 + k)].x, pts[(size_t) (12 + k)].y, pts[(size_t) (12 + k)].z }; sc.setControls (kGb + 48 + k * 3, q, 3); }
    }
    // meters back from the server
    follow = sc.controlBus (kGb + 16); outEnv = sc.controlBus (kGb + 17); natEnv = jlimit (0.0f, 1.0f, sc.controlBus (kGb + 20) * 7.0f);
    {   // followers with their own attack / release / gain
        static thread_local float f = 0, o = 0;
        const float ca = 1.0f - std::exp (-dt / jmax (eff[(size_t) id->fAtt], 0.001f)), cr = 1.0f - std::exp (-dt / jmax (eff[(size_t) id->fRel], 0.005f));
        const float tf = jlimit (0.0f, 1.0f, std::sqrt (follow * eff[(size_t) id->fGain] * 6.0f)), to = jlimit (0.0f, 1.0f, std::sqrt (outEnv * 5.0f));
        f += (tf - f) * (tf > f ? ca : cr); o += (to - o) * (to > o ? ca : cr);
        follow = f; outEnv = o;
    }
    view.vuL = sc.controlBus (kGb + 18); view.vuR = sc.controlBus (kGb + 19); view.follow = follow; view.outEnv = outEnv;
    view.lfo1 = lfoVal[0]; view.lfo2 = lfoVal[1]; view.lorX = lorX; view.lorY = lorY; view.lorZ = lorZ;
    for (int b = 0; b < 8; ++b) { view.boidX[(size_t) b] = boidX[b]; view.boidY[(size_t) b] = boidY[b]; }
}

void Engine::rebuildPins()
{
    pins.clear();
    for (const auto& p : pinIds)
    {
        const float a = params.get (p[0]);
        if (std::fabs (a) > 0.0005f && p[1] > 0 && p[1] < kSrc && p[2] > 0 && p[2] < nDst && pins.size() < 128) pins.push_back ({ p[1], p[2], a });
    }
}

// ------------------------------------------------------------------------------------------------ global modulators
void Engine::updateGlobals (float d)
{
    // matrix pins from global sources to the LFO rates (destinations 13, 14)
    const float gsrc[kSrc] = { 0, lfoVal[0], lfoVal[1], 0, 0, 0, 0, wheel, pressure, 0, chaos, natEnv, follow, outEnv, boidX[0], boidY[0], lorX, lorY, lorZ, ccSm[0], ccSm[1], ccSm[2], ccSm[3] };
    float d13 = 0, d14 = 0;
    for (const auto& p : pins) { if (p.dst == 13) d13 += p.amt * gsrc[p.src]; else if (p.dst == 14) d14 += p.amt * gsrc[p.src]; }
    // LFOs: 1 sine 2 triangle 3 saw 4 square 5 sample & hold 6 smooth random
    for (int l = 0; l < 2; ++l)
    {
        float rate = eff[(size_t) (l == 0 ? id->l1Rate : id->l2Rate)] * std::pow (2.0f, (l == 0 ? d13 : d14) * 3.0f);
        if (params.get (l == 0 ? id->l1Sync : id->l2Sync) > 0.5f)
        {
            float best = rate, bestD = 1e9f;
            for (float dv : kSyncDivs) { const float r = (float) bpm / 60.0f / dv; const float e = std::fabs (std::log (r / jmax (rate, 0.001f))); if (e < bestD) { bestD = e; best = r; } }
            rate = best;
        }
        lfoPh[l] += rate * d;
        bool wrapped = false;
        if (lfoPh[l] >= 1.0f) { lfoPh[l] -= std::floor (lfoPh[l]); wrapped = true; }
        if (wrapped) { lfoSh[l] = lfoShNext[l]; lfoShNext[l] = rnd (-1, 1); }
        const float ph = lfoPh[l];
        switch ((int) std::lrint (params.get (l == 0 ? id->l1Shape : id->l2Shape)))
        {
            case 1: lfoVal[l] = std::sin (6.2831853f * ph); break;
            case 2: lfoVal[l] = ph < 0.5f ? 4.0f * ph - 1.0f : 3.0f - 4.0f * ph; break;
            case 3: lfoVal[l] = 2.0f * ph - 1.0f; break;
            case 4: lfoVal[l] = ph < 0.5f ? 1.0f : -1.0f; break;
            case 5: lfoVal[l] = lfoSh[l]; break;
            default: { const float t = ph * ph * (3.0f - 2.0f * ph); lfoVal[l] = lfoSh[l] + (lfoShNext[l] - lfoSh[l]) * t; } break;
        }
    }
    // boids: 8 agents in a box
    {
        const float bs = eff[(size_t) id->bSpeed], co = eff[(size_t) id->bCoh], se = eff[(size_t) id->bSep], al = eff[(size_t) id->bAli];
        const float vmax = (0.0006f + bs * bs * 0.02f) * (d * 750.0f);
        for (int b = 0; b < 8; ++b)
        {
            float cx = 0, cy = 0, ax = 0, ay = 0, sx = 0, sy = 0; int nn = 0;
            for (int j = 0; j < 8; ++j)
            {
                if (j == b) continue;
                const float dx = boidX[j] - boidX[b], dy = boidY[j] - boidY[b], d2 = dx * dx + dy * dy;
                if (d2 < 0.6f) { cx += dx; cy += dy; ax += boidVX[j]; ay += boidVY[j]; ++nn; if (d2 < 0.05f) { sx -= dx / (d2 + 0.002f); sy -= dy / (d2 + 0.002f); } }
            }
            float vx = boidVX[b], vy = boidVY[b];
            if (nn > 0) { vx += cx / nn * co * vmax * 0.06f + (ax / nn - vx) * al * 0.08f; vy += cy / nn * co * vmax * 0.06f + (ay / nn - vy) * al * 0.08f; }
            vx += sx * se * vmax * 0.0015f; vy += sy * se * vmax * 0.0015f;
            const float px = boidX[b], py = boidY[b];
            vx -= px * px * px * vmax * 0.25f; vy -= py * py * py * vmax * 0.25f;
            vx += rnd (-1, 1) * vmax * 0.08f; vy += rnd (-1, 1) * vmax * 0.08f;
            const float v = std::sqrt (vx * vx + vy * vy);
            if (v > vmax && v > 0) { vx *= vmax / v; vy *= vmax / v; }
            boidVX[b] = vx; boidVY[b] = vy; boidX[b] = jlimit (-1.0f, 1.0f, px + vx); boidY[b] = jlimit (-1.0f, 1.0f, py + vy);
        }
    }
    // Lorenz attractor
    {
        const float lr = eff[(size_t) id->lRate], sg = eff[(size_t) id->lSigma], ro = eff[(size_t) id->lRho], be = eff[(size_t) id->lBeta];
        const float ldt = (0.05f + lr * lr * 4.0f) * d;
        for (int k = 0; k < 4; ++k)
        {
            const float dx = sg * (ly - lx), dy = lx * (ro - lz) - ly, dz = lx * ly - be * lz;
            lx += dx * ldt * 0.25f; ly += dy * ldt * 0.25f; lz += dz * ldt * 0.25f;
        }
        if (! (std::fabs (lx) < 1000 && std::fabs (ly) < 1000 && std::fabs (lz) < 1000)) { lx = 0.1f; ly = 0; lz = 20; }
        lorX = jlimit (-1.0f, 1.0f, lx / 20.0f); lorY = jlimit (-1.0f, 1.0f, ly / 27.0f); lorZ = jlimit (-1.0f, 1.0f, (lz - ro + 1.0f) / (ro * 0.8f + 1.0f));
        chaos = lorX;
    }
    // MIDI CC rows, smoothed
    for (int k = 0; k < 4; ++k) { const float t = cc[(size_t) jlimit (0, 127, (int) std::lrint (params.get (ccnIds[(size_t) k])))]; ccSm[(size_t) k] += (t - ccSm[(size_t) k]) * jmin (1.0f, d / 0.01f); }
    // the field loops' slow drift
    if (rnd (0, 1) < d / 4.0f) lpAt = rnd (0, 1);
    if (rnd (0, 1) < d / 4.7f) lpBt = rnd (0, 1);
    lpA += (lpAt - lpA) * d * 0.4f; lpB += (lpBt - lpB) * d * 0.4f;
}

// ------------------------------------------------------------------------------------------------ sampler (nature scenes, bed)
void Engine::updateSampler()
{
    int sel = samplerSel < 1 ? 1 : samplerSel;
    for (int i = 0; i < 26; ++i) if (params.get (sIds[(size_t) i]) > 0.5f) { sel = i + 1; break; }
    const float samp = eff[(size_t) id->AmpSamp];
    const bool wantNat = sel <= 8 && (samp > 0.0005f || eff[(size_t) id->resonate] > 0.001f);
    const bool wantBed = sel > 8 && samp > 0.0005f && numFiles > 0;
    if (sel != samplerSel || wantNat != natOn || wantBed != bedOn)
    {
        if (natOn) sc.send (OscMsg ("/n_free").i (20));
        if (bedOn) { if (sonic) for (int k = 0; k < 6; ++k) sc.send (OscMsg ("/n_free").i (21 + k)); else sc.send (OscMsg ("/n_free").i (21)); }
        natOn = wantNat; bedOn = wantBed; samplerSel = sel; view.sampler = sel;
        if (natOn) sc.send (OscMsg ("/s_new").s (("oNat" + std::to_string (sel)).c_str()).i (20).i (0).i (0).s ("natbus").i (aNat));
        fieldNorm = (sel > 8 && sel - 9 < (int) fnorm.size()) ? fnorm[(size_t) (sel - 9)] : 1.0f;
        if (bedOn)
        {
            if (sonic)
                for (int k = 0; k < 6; ++k)
                    sc.send (OscMsg ("/s_new").s ("oBedS").i (21 + k).i (0).i (0).s ("amb").i (aAmb).s ("buf").i (sel - 9).s ("norm").f (fieldNorm)
                                 .s ("kpos").i (kGb + 48 + k * 3).s ("ch").i (k % 2).s ("drift").f (0.12f));
            else
                sc.send (OscMsg ("/s_new").s ("oBed").i (21).i (0).i (0).s ("fieldbus").i (aField).s ("buf").i (sel - 9).s ("norm").f (fieldNorm).s ("drift").f (0.1f));
        }
    }
    if (bedOn)
    {
        const float gain = 0.6f * (1.0f - std::exp (-samp * 25.0f / 0.6f));
        const int nb = sonic ? 6 : 1;
        static thread_local float lastGain = -1, lastRate = -1, lastRev = -1;
        const float rate = eff[(size_t) id->fSpeed], rev = params.get (id->fRev);
        if (std::fabs (gain - lastGain) > 0.0005f || std::fabs (rate - lastRate) > 0.0005f || rev != lastRev)
        {
            lastGain = gain; lastRate = rate; lastRev = rev;
            for (int k = 0; k < nb; ++k)
            {
                OscMsg m ("/n_set"); m.i (21 + k).s ("gain").f (gain).s ("rate").f (rate).s ("rev").f (rev);
                if (sonic) m.s ("spread").f (eff[(size_t) id->spSpread]).s ("air").f (eff[(size_t) id->spAir]).s ("dopp").f (eff[(size_t) id->spDopp]).s ("ref").f (1.0f + (eff[(size_t) id->spDist] - 1.0f) * 0.5f);
                sc.send (m);
            }
        }
    }
}

// ------------------------------------------------------------------------------------------------ one voice
void Engine::updateVoice (Voice& v, float d)
{
    // ---- envelopes and lifetime
    float aenv = v.amp.tick (d);
    const float fenv = v.filt.tick (d);
    v.menvT += d;
    v.menv = v.menvT < v.meA ? v.menvT / v.meA : jmax (0.0f, 1.0f - (v.menvT - v.meA) / v.meD);
    if (v.drone)
    {
        // VCA INIT: after the key goes up the voice falls to the INIT level; the last chord (at most 8 notes) keeps droning
        const bool keep = v.gen == generation && noteCounter - v.order < 8;
        v.alive += ((keep ? 1.0f : 0.0f) - v.alive) * jmin (1.0f, d / 0.08f);
        if (! v.held && v.amp.stage < 3) v.amp.release();
        const float floor = eff[(size_t) id->VCAinit] * v.alive;
        if (! v.held && aenv < 0.0005f && floor < 0.0005f) ++v.ended;
        aenv = jmax (aenv, floor);
    }
    else if (v.amp.stage >= 4) ++v.ended;

    // ---- modulation matrix
    const float bx = boidX[v.slot % 8], by = boidY[v.slot % 8], bv = params.get (id->scBoidV);
    const float S[kSrc] = { 0, lfoVal[0], lfoVal[1], v.menv, aenv, v.vel, (float) (v.note - 60) / 24.0f, wheel, pressure, v.rnd, chaos, natEnv, follow, outEnv,
                            bx * bv, by * bv, lorX, lorY, lorZ, ccSm[0], ccSm[1], ccSm[2], ccSm[3] };
    float D[kDstMax] = {};
    for (const auto& p : pins) D[p.dst] += p.amt * S[p.src];
    auto src = [&] (int idx) -> float { const int s = (int) params.get (idx) - 1; return (s > 0 && s < kSrc) ? S[s] : 0.0f; };

    // ---- pitch
    v.glide += ((float) v.note - v.glide) * v.glideCoef;
    const float oct = params.get (id->OctDn) > 0.5f ? -12.0f : (params.get (id->OctUp) > 0.5f ? 12.0f : 0.0f);
    const float pitch = lfoVal[1] * P (id->vib) + v.menv * P (id->pEnv) * 24.0f + v.glide + P (id->VCO) + oct
                        + 12.0f * std::log2 (jmax (P (id->Tune1), 0.01f)) + D[1] * 12.0f + bend * P (id->bendRange);
    const float freq = jlimit (4.0f, (float) sr * 0.45f, mtof (pitch));

    float k[kKn] = {};
    k[kFreq] = freq;
    k[kPw] = P (id->pw) + D[4] * 0.45f;
    k[kDetune] = jlimit (0.0f, 2.0f, P (id->detune) + D[10]);
    k[kDrift] = P (id->drift); k[kSpread] = P (id->spread);
    k[kVco] = P (id->ampVCO) * 0.5f;
    k[kSub] = jlimit (0.0f, 1.0f, P (id->sub) + D[7]); k[kSub2] = params.get (id->sub2);
    k[kFm] = jlimit (0.0f, 1.0f, P (id->fm) + D[6]); k[kFmRatio] = P (id->fmRatio);
    k[kFold] = jlimit (0.0f, 1.0f, P (id->fold) + D[5]);
    k[kNoise] = jlimit (0.0f, 1.0f, P (id->noise) + D[8] * 0.5f); k[kTone] = jlimit (1.0f, 12000.0f, P (id->tone));
    k[kReson] = jlimit (0.0f, 1.0f, P (id->resonate) + D[9]);

    // ---- filters: A = the top panel (with the envelope), B = the Lester page; six CV inputs
    float La[4] = {}, Lb[4] = {};
    for (int j = 0; j < 6; ++j)
    {
        const float val = params.get (lAtt[(size_t) j]) * src (lSrc[(size_t) j]);
        const int dd = lDst[(size_t) j] < 0 ? 0 : jlimit (0, 3, (int) params.get (lDst[(size_t) j]) - 1);
        (j < 3 ? La : Lb)[dd] += val;
    }
    const float cmax = jmin (18000.0f, (float) sr * 0.42f);
    const float octA = std::log2 (P (id->LPFreq)) - P (id->mod) * (1.0f - fenv) * 6.0f + D[2] * 5.0f + La[0] * 5.0f;
    float cA = jlimit (25.0f, cmax, std::pow (2.0f, octA));
    float rA = jlimit (0.0f, 1.0f, P (id->Res) + D[3] * 0.5f + La[1]);
    float mA = jlimit (0.0f, 4.0f, P (id->aMode) + D[34] * 4.0f + La[2] * 4.0f);
    float gA = jlimit (0.0f, 1.0f, P (id->aGain) + La[3] * 0.5f + D[36] * 0.5f);
    const int link = (int) std::lrint (params.get (id->link));
    float cB = cA, rB = rA, mB = mA, gB = gA;
    if (link != 4 && link != 5)
    {
        float octB = std::log2 (P (id->bCut)) + D[33] * 5.0f + Lb[0] * 5.0f;
        if (link == 2) octB += octA - 9.3f;
        cB = jlimit (25.0f, cmax, std::pow (2.0f, octB));
        rB = jlimit (0.0f, 1.0f, P (id->bRes) + Lb[1]);
        mB = jlimit (0.0f, 4.0f, P (id->bMode) + D[34] * 4.0f + Lb[2] * 4.0f);
        gB = jlimit (0.0f, 1.0f, P (id->bGain) + Lb[3] * 0.5f + D[36] * 0.5f);
    }
    k[kCutA] = cA; k[kResA] = rA; k[kModeA] = mA; k[kGainA] = gA; k[kCutB] = cB; k[kResB] = rB; k[kModeB] = mB; k[kGainB] = gB;
    k[kLMix] = jlimit (0.0f, 1.0f, P (id->lMix) + D[35]);
    if (v.order == noteCounter) { view.cutA = cA; view.cutB = cB; view.resA = rA; view.resB = rB; view.modeA = mA; view.modeB = mB; }

    // ---- amp, pan, sends
    const float vel = 1.0f - P (id->velAmt) + P (id->velAmt) * v.vel;
    k[kAmp] = aenv * jlimit (0.0f, 2.0f, (1.0f + D[11]) * vel);
    k[kPan] = jlimit (0.0f, 1.0f, 0.5f + D[12] * 0.5f + v.rnd * P (id->vStereo) * 0.5f);
    k[kDly] = jlimit (0.0f, 2.0f, 1.0f + D[15]); k[kRev] = jlimit (0.0f, 2.0f, 1.0f + D[16]);
    k[kDrive] = P (id->drive);

    // ---- polygon: six jacks (source x attenuverter) and the matrix
    float J[6]; for (int j = 0; j < 6; ++j) J[j] = params.get (jAtt[(size_t) j]) * src (jSrc[(size_t) j]);
    float po = P (id->pOrder) + J[1] * 5.0f + D[17] * 5.0f;
    if (params.get (id->pRegular) > 0.5f) po = std::round (po);
    po = jlimit (2.05f, 32.0f, po);
    const float pt = jlimit (0.0f, 1.0f, P (id->pTeeth) + J[2] + D[18]);
    const float sl = P (id->pSlew) > 0.0005f ? 1.0f - std::exp (-d * 0.6931f / P (id->pSlew)) : 1.0f;
    v.order_s += (po - v.order_s) * (d > 0 ? sl : 1.0f); v.teeth_s += (pt - v.teeth_s) * (d > 0 ? sl : 1.0f);
    v.spin += P (id->pSpin) * d;
    float pq = P (id->pRatio) * std::pow (2.0f, J[4] * 2.0f);
    if (params.get (id->pSnap) > 0.5f) pq = pq < 0.75f ? 0.5f : std::round (pq);
    k[kPFreq] = jlimit (2.0f, (float) sr * 0.4f, mtof (pitch + P (id->pTune) + J[0] * 24.0f));
    k[kPOrder] = v.order_s; k[kPTeeth] = v.teeth_s; k[kPRoll] = P (id->pRoll) + J[3] + D[19] + v.spin; k[kPRatio] = pq;
    k[kPAmt] = jlimit (0.0f, 1.0f, P (id->pAmt) + J[5] + D[20]); k[kPFold] = jlimit (0.0f, 1.0f, P (id->pFold) + D[22]);
    k[kPLevel] = jlimit (0.0f, 1.0f, P (id->pLevel) + D[21]); k[kPWidth] = P (id->pWidth); k[kPFm] = P (id->pFM); k[kPSkew] = P (id->pPhase);

    // ---- Odessa: four CV sliders (exp FM, lin FM, density, warp) and the matrix
    float OC[4]; for (int j = 0; j < 4; ++j) OC[j] = params.get (oCvA[(size_t) j]) * src (oCvS[(size_t) j]);
    k[kOFreq] = jlimit (1.0f, (float) sr * 0.45f, freq * semi (P (id->oTune) + P (id->oFine) / 100.0f + OC[0] * 24.0f) * std::fabs (1.0f + OC[1] * 2.0f));
    k[kOLevel] = jlimit (0.0f, 1.0f, P (id->oLevel) + D[29]);
    k[kOPart] = jlimit (1.0f, 128.0f, P (id->oPart) + D[23] * 64.0f);
    k[kOTilt] = jlimit (0.0f, 1.0f, P (id->oTilt) + D[24]); k[kOTens] = jlimit (-1.0f, 1.0f, P (id->oTension) + D[25]);
    k[kODens] = jlimit (0.0f, 1.0f, P (id->oDens) + OC[2] + D[26]); k[kOWarp] = jlimit (0.0f, 1.0f, P (id->oWarp) + OC[3] + D[27]);
    k[kOPeak] = jlimit (0.0f, 1.0f, P (id->oPeak) + D[28]); k[kOFund] = P (id->oFund); k[kOWidth] = P (id->oWidth); k[kOSpread] = P (id->oSpread);

    // ---- the recording played from the keys
    const float fl = jlimit (0.0f, 1.0f, P (id->fVoice) + D[32]);
    k[kFLevel] = fl * fl * 1.1f * fieldNorm;
    float fr = semi (P (id->fPitch));
    if (params.get (id->fKey) > 0.5f) fr *= semi (pitch - 60.0f - oct - P (id->VCO));
    k[kFRate] = fr;
    k[kFPos] = jlimit (0.0f, 0.97f, P (id->fPos) + D[30] + v.scat * P (id->fScatter) * 0.5f + (lpA - 0.5f) * 0.24f);
    k[kFSize] = jlimit (0.003f, 1.0f, (P (id->fSize) + D[31]) * (0.6f + lpB * 0.8f));

    // ---- where this voice is (ObliqSonic): its bird, pushed by the matrix's space destinations
    if (sonic)
    {
        const auto& q = pts[(size_t) (v.slot % 12)];
        const float dist = eff[(size_t) id->spDist];
        const float dsc = std::pow (2.0f, jlimit (-3.0f, 3.0f, D[37] * 2.0f));
        const float az = D[38] * 3.14159f + D[12] * 1.5708f + v.rnd * P (id->vStereo) * 0.8f;
        const float dv = D[41] * dist * 0.6f;
        k[kX] = (q.x * std::cos (az) - q.y * std::sin (az)) * dsc + v.rx * dv;
        k[kY] = (q.x * std::sin (az) + q.y * std::cos (az)) * dsc + v.ry * dv;
        k[kZ] = q.z * dsc + D[39] * dist + v.rz * dv * 0.6f;
        k[kSpSpread] = jlimit (0.0f, 1.0f, eff[(size_t) id->spSpread] + D[40]); k[kSpAir] = jlimit (0.0f, 1.0f, eff[(size_t) id->spAir] + D[42]);
    }
    sc.setControls (kKb0 + v.slot * kKn, k, kKn - 2);        // the last two are written by the polygon synth (XY screen)
    if (v.order == noteCounter && v.hasPoly) { view.polyX = sc.controlBus (kKb0 + v.slot * kKn + kKn - 2); view.polyY = sc.controlBus (kKb0 + v.slot * kKn + kKn - 1); }
}

// ------------------------------------------------------------------------------------------------ space (ObliqSonic)
// 22 points: flock (3-D boids) > deviated Lorenz (one attractor per point) > gravity (three orbiting wells). MODE morphs.
void Engine::updateSpace (float d)
{
    spAcc += d;
    const float speed = eff[(size_t) id->spSpeed], dev = eff[(size_t) id->spDev], dist = eff[(size_t) id->spDist];
    if (spAcc >= 0.025f)
    {
        const float h = spAcc; spAcc = 0;
        const float spd = 0.08f + speed * 1.4f;
        // flock
        float cx = 0, cy = 0, cz = 0, mx = 0, my = 0, mz = 0;
        for (auto& q : pts) { cx += q.fx; cy += q.fy; cz += q.fz; mx += q.vx; my += q.vy; mz += q.vz; }
        cx /= kPoints; cy /= kPoints; cz /= kPoints; mx /= kPoints; my /= kPoints; mz /= kPoints;
        leadT += h * (0.08f + speed * 0.7f);
        const float ldx = 0.72f * std::cos (leadT), ldy = 0.72f * std::sin (leadT * 1.13f), ldz = 0.35f * std::sin (leadT * 0.61f);
        const float coh = 0.2f + eff[(size_t) id->spCoh] * 1.6f;
        for (int i = 0; i < kPoints; ++i)
        {
            auto& q = pts[(size_t) i];
            float sx = 0, sy = 0, sz = 0;
            for (int j = 0; j < kPoints; ++j)
            {
                if (j == i) continue;
                const auto& o = pts[(size_t) j];
                const float dx = q.fx - o.fx, dy = q.fy - o.fy, dz = q.fz - o.fz, d2 = dx * dx + dy * dy + dz * dz;
                if (d2 < 0.1f) { const float iv = 1.0f / (d2 + 0.02f); sx += dx * iv; sy += dy * iv; sz += dz * iv; }
            }
            float ax = ((cx + ldx) * 0.5f - q.fx) * coh + sx * 0.025f + (mx - q.vx) * 0.8f + rnd (-1, 1) * 0.6f * spd;
            float ay = ((cy + ldy) * 0.5f - q.fy) * coh + sy * 0.025f + (my - q.vy) * 0.8f + rnd (-1, 1) * 0.6f * spd;
            float az = ((cz + ldz) * 0.5f - q.fz) * coh + sz * 0.025f + (mz - q.vz) * 0.8f + rnd (-1, 1) * 0.4f * spd;
            const float pr = std::sqrt (q.fx * q.fx + q.fy * q.fy + q.fz * q.fz);
            if (pr > 1.0f) { ax -= q.fx * (pr - 1.0f) * 6.0f; ay -= q.fy * (pr - 1.0f) * 6.0f; az -= q.fz * (pr - 1.0f) * 6.0f; }
            else if (pr < 0.35f) { const float pi = (0.35f - pr) * 4.0f / jmax (pr, 0.05f); ax += q.fx * pi; ay += q.fy * pi; az += q.fz * pi; }
            ax += -q.fy * 0.25f * spd; ay += q.fx * 0.25f * spd;
            q.vx += ax * h; q.vy += ay * h; q.vz += az * h;
            const float vv = std::sqrt (q.vx * q.vx + q.vy * q.vy + q.vz * q.vz);
            if (vv > spd) { q.vx *= spd / vv; q.vy *= spd / vv; q.vz *= spd / vv; }
            q.fx += q.vx * h; q.fy += q.vy * h; q.fz += q.vz * h;
        }
        // deviated Lorenz: every point its own attractor, turned to its own heading
        const float ldt = (0.0015f + speed * 0.012f) * 1.25f;
        float hx[kPoints], hy[kPoints], hz[kPoints];
        for (int i = 0; i < kPoints; ++i)
        {
            auto& q = pts[(size_t) i];
            const float sg = 10.0f * (1.0f + q.ds * dev * 0.4f), ro = 28.0f * (1.0f + q.dr * dev * 0.3f);
            for (int s = 0; s < 4; ++s)
            {
                const float x = q.lx, y = q.ly, z = q.lz;
                q.lx = x + sg * (y - x) * ldt; q.ly = y + (x * (ro - z) - y) * ldt; q.lz = z + (x * y - 2.6667f * z) * ldt;
            }
            if (! (std::fabs (q.lx) < 500 && std::fabs (q.ly) < 500 && std::fabs (q.lz) < 500)) { q.lx = rnd (-8, 8); q.ly = rnd (-8, 8); q.lz = rnd (18, 32); }
            const float hd = (float) i * 6.2832f / kPoints * (0.15f + dev * 0.85f), ux = q.lx / 13.0f, uy = q.ly / 15.0f;
            hx[i] = ux * std::cos (hd) - uy * std::sin (hd); hy[i] = ux * std::sin (hd) + uy * std::cos (hd); hz[i] = (q.lz - 25.0f) / 15.0f;
        }
        // gravity: three wells on slow orbits
        wellT += h * (0.05f + speed * 0.4f);
        const float w[3][3] = { { 0.75f * std::cos (wellT), 0.75f * std::sin (wellT), 0.3f * std::sin (wellT * 0.7f) },
                                { 0.6f * std::cos (-wellT * 1.37f + 2.1f), 0.6f * std::sin (-wellT * 1.37f + 2.1f), -0.35f * std::cos (wellT * 0.53f) },
                                { 0.4f * std::cos (wellT * 0.61f + 4.2f), 0.85f * std::sin (wellT * 0.61f + 4.2f), 0.5f * std::sin (wellT * 1.1f + 1.0f) } };
        const float gg = 0.05f + eff[(size_t) id->spGrav] * 0.6f;
        for (auto& q : pts)
        {
            float ax = 0, ay = 0, az = 0;
            for (int k = 0; k < 3; ++k)
            {
                const float dx = w[k][0] - q.gx, dy = w[k][1] - q.gy, dz = w[k][2] - q.gz;
                const float d3 = std::pow (dx * dx + dy * dy + dz * dz + 0.04f, 1.5f);
                ax += dx / d3; ay += dy / d3; az += dz / d3;
            }
            q.qx = (q.qx + ax * gg * h) * 0.9985f; q.qy = (q.qy + ay * gg * h) * 0.9985f; q.qz = (q.qz + az * gg * h) * 0.9985f;
            const float vv = std::sqrt (q.qx * q.qx + q.qy * q.qy + q.qz * q.qz), vm = spd * 1.6f;
            if (vv > vm) { q.qx *= vm / vv; q.qy *= vm / vv; q.qz *= vm / vv; }
            q.gx += q.qx * h; q.gy += q.qy * h; q.gz += q.qz * h;
            const float pr = std::sqrt (q.gx * q.gx + q.gy * q.gy + q.gz * q.gz);
            if (pr > 1.1f) { q.gx *= 1.1f / pr; q.gy *= 1.1f / pr; q.gz *= 1.1f / pr; q.qx *= 0.5f; q.qy *= 0.5f; q.qz *= 0.5f; }
        }
        // blend, deviate, turn, scale
        yaw += h * eff[(size_t) id->spRot] * 0.6283f;
        const float md = eff[(size_t) id->spMode];
        float wF = jlimit (0.0f, 1.0f, 1.0f - md), wL = jlimit (0.0f, 1.0f, 1.0f - std::fabs (md - 1.0f)), wG = jlimit (0.0f, 1.0f, md - 1.0f);
        const float nb = 1.0f / std::sqrt (wF * wF + wL * wL + wG * wG + 0.0001f); wF *= nb; wL *= nb; wG *= nb;
        view.spMode = md;
        float fcx = 0, fcy = 0, fcz = 0;
        for (int i = 0; i < kPoints; ++i)
        {
            auto& q = pts[(size_t) i];
            if (rnd (0, 1) < 0.01f + speed * 0.025f) { q.wx = rnd (-1, 1); q.wy = rnd (-1, 1); q.wz = rnd (-1, 1); }
            q.ox += (q.wx - q.ox) * 0.02f; q.oy += (q.wy - q.oy) * 0.02f; q.oz += (q.wz - q.oz) * 0.02f;
            const float x = wF * q.fx + wL * hx[i] + wG * q.gx + q.ox * dev * 0.35f;
            const float y = wF * q.fy + wL * hy[i] + wG * q.gy + q.oy * dev * 0.35f;
            const float z = (wF * q.fz + wL * hz[i] + wG * q.gz + q.oz * dev * 0.25f) * eff[(size_t) id->spHeight];
            q.tx = (x * std::cos (yaw) - y * std::sin (yaw)) * dist; q.ty = (x * std::sin (yaw) + y * std::cos (yaw)) * dist; q.tz = z * dist;
            if (i >= 12 && i < 18) { fcx += q.tx / 6.0f; fcy += q.ty / 6.0f; fcz += q.tz / 6.0f; }
        }
        const float sp = 0.15f + eff[(size_t) id->spFSplay] * 1.1f;
        for (int i = 12; i < 18; ++i) { auto& q = pts[(size_t) i]; q.tx = fcx + (q.tx - fcx) * sp; q.ty = fcy + (q.ty - fcy) * sp; q.tz = fcz + (q.tz - fcz) * sp; }
    }
    const float c = jmin (1.0f, d / 0.17f);
    for (int i = 0; i < kPoints; ++i)
    {
        auto& q = pts[(size_t) i];
        q.x += (q.tx - q.x) * c; q.y += (q.ty - q.y) * c; q.z += (q.tz - q.z) * c;
        view.px[(size_t) i] = q.x; view.py[(size_t) i] = q.y; view.pz[(size_t) i] = q.z;
    }
}

// ------------------------------------------------------------------------------------------------ RANDOMIZE
void Engine::randomize()
{
    auto roll = [this] (const char* name, float scale = 1.0f)
    {
        const int i = params.find (name); if (i < 0) return;
        const auto& d = params.def (i);
        params.set (i, params.fromNorm (i, rnd (0, 1) * scale));
    };
    for (auto n : { "LPFreq", "Res", "aMode", "aGain", "bCut", "bRes", "bMode", "bGain", "mod", "FAtt", "FDec", "FSus", "FRel", "pw", "Tune1", "detune",
                    "pOrder", "pTeeth", "pRoll", "pRatio", "pAmt", "oPart", "oTilt", "oTension", "oDens", "oWarp", "oPeak", "chorus", "space", "fPos", "fSize" }) roll (n);
    for (auto n : { "noise", "pLevel", "oLevel", "reverb", "drive" }) roll (n, 0.6f);
    params.set (id->waveform, (float) (1 + (int) (rng() % 4)));
    const int sq = (int) (rng() % 26);
    for (int i = 0; i < 26; ++i) params.set (sIds[(size_t) i], i == sq ? 1.0f : 0.0f);
    params.set (id->AmpSamp, rnd (0.03f, 0.12f));
    if (sonic) for (auto n : { "spMode", "spSpeed", "spDev", "spGrav", "spCoh", "spFSplay", "spHeight" }) roll (n, 0.85f);
}
