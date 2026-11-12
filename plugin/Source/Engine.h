// Engine: voice management and every modulator of ObliqSound / ObliqSonic, computed once per 64-sample
// block and written straight into the embedded SuperCollider server's control buses.
#pragma once
#include "Params.h"
#include "../../sc/ScEngine.h"
#include <juce_audio_basics/juce_audio_basics.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <array>
#include <random>

class Engine
{
public:
    enum { kVoices = 16, kKn = 60, kKb0 = 128, kPoints = 22, kSrc = 23, kDstMax = 44 };

    Engine (ParamStore& p, bool sonic, const juce::var& layout);
    ~Engine();

    bool prepare (double sampleRate, const juce::File& resources);
    void release();
    void process (juce::AudioBuffer<float>& out, const juce::MidiBuffer& midi, double bpm);
    void allNotesOff();
    int numOutputs() const { return sonic ? 16 : 2; }
    bool ready() const { return sc.isRunning(); }
    juce::String lastError;

    // ---- read by the editor (written by the audio thread, plain floats)
    struct View
    {
        std::atomic<float> lfo1 { 0 }, lfo2 { 0 }, vuL { 0 }, vuR { 0 }, follow { 0 }, outEnv { 0 };
        std::atomic<float> lorX { 0 }, lorY { 0 }, lorZ { 0 };
        std::array<std::atomic<float>, 8> boidX, boidY;
        std::array<std::atomic<float>, kPoints> px, py, pz;
        std::atomic<float> polyX { 0 }, polyY { 0 };
        std::atomic<int> voices { 0 }, sampler { 1 };
        std::atomic<float> cutA { 0 }, cutB { 0 }, resA { 0 }, resB { 0 }, modeA { 0 }, modeB { 0 }, spMode { 0 };
        std::atomic<float> cpu { 0 };
    } view;

private:
    struct Env
    {
        float a = 0.01f, d = 0.1f, s = 0.7f, r = 0.2f, v = 0, relStart = 0; int stage = 0;   // 0 attack 1 decay 2 sustain 3 release 4 done
        void start() { stage = 0; }
        void release() { if (stage < 3) { stage = 3; relStart = v; } }
        float tick (float dt)
        {
            switch (stage)
            {
                case 0: v += dt / a; if (v >= 1.0f) { v = 1.0f; stage = 1; } break;
                case 1: v -= dt / d * (1.0f - s); if (v <= s) { v = s; stage = 2; } break;
                case 2: v = s; break;
                case 3: v -= dt / r * juce::jmax (relStart, 0.0001f); if (v <= 0.0f) { v = 0.0f; stage = 4; } break;
                default: v = 0.0f; break;
            }
            return v;
        }
    };
    struct Voice
    {
        bool active = false, held = false, drone = false, stolen = false, hasPoly = false, hasOde = false, hasField = false;
        int note = 60, group = 0, order = 0, gen = 0, slot = 0;
        float vel = 1, rnd = 0, scat = 0, rx = 0, ry = 0, rz = 0;
        float glide = 60, glideCoef = 1, menv = 0, menvT = 0, alive = 1, fade = 1, spin = 0, order_s = 4, teeth_s = 0, cutA = 1000, cutB = 1000;
        float meA = 0.005f, meD = 0.45f;
        Env amp, filt;
        int ended = 0;
    };

    void tick();                                    // one 64-sample block
    void handleMidi (const juce::MidiMessage&);
    void noteOn (int note, float vel);
    void noteOff (int note);
    void startVoice (Voice&, int note, float vel);
    void freeVoice (Voice&);
    void updateGlobals (float dt);
    void updateVoice (Voice&, float dt);
    void updateSpace (float dt);
    void updateSampler();
    void rebuildPins();
    void randomize();
    float P (int idx) const { return eff[(size_t) idx]; }
    int pid (const char* id) { return params.find (id); }
    void loadSamples (const juce::File& dir);

    ParamStore& params;
    const bool sonic;
    ScEngine sc;
    double sr = 48000.0;
    float dt = 64.0f / 48000.0f;
    double bpm = 120.0;
    std::vector<float> eff;                         // parameter values this block, after the swarm
    std::mt19937 rng { 0x0b11c5 };
    float rnd (float lo, float hi) { return lo + (hi - lo) * (float) (rng() & 0xffffff) / (float) 0xffffff; }

    // bus numbers
    int aBase = 4, aMix = 4, aDly = 6, aRev = 8, aField = 10, aNat = 12, aAmb = 14, aVoice0 = 30;
    enum { kGb = 0 };

    // voices
    std::array<Voice, kVoices> voices;
    int noteCounter = 0, generation = 0, heldCount = 0, nextGroup = 1000;
    float lastPitch = 60;
    float bend = 0, wheel = 0, pressure = 0;
    std::array<float, 128> cc {};
    std::array<float, 4> ccSm {};

    // modulators
    float lfoPh[2] = { 0, 0 }, lfoVal[2] = { 0, 0 }, lfoSh[2] = { 0, 0 }, lfoShNext[2] = { 0, 0 };
    float boidX[8], boidY[8], boidVX[8], boidVY[8];
    float lx = 0.1f, ly = 0, lz = 20, lorX = 0, lorY = 0, lorZ = 0, chaos = 0;
    float follow = 0, outEnv = 0, natEnv = 0, lpA = 0.5f, lpB = 0.5f, lpAt = 0.5f, lpBt = 0.5f;
    float globalD13 = 0, globalD14 = 0;

    // matrix
    struct Pin { int src, dst; float amt; };
    std::vector<Pin> pins;
    std::vector<std::array<int, 3>> pinIds;         // param index, src, dst
    int pinCounter = 0, lastChange = -1;
    int nDst = 37;

    // swarm
    struct Sw { int idx, sec, boid, lor; bool axisY, mul; float sign, amt, lo, hi; };
    std::vector<Sw> swarm;

    // sampler
    int samplerSel = -1; bool natOn = false, bedOn = false;
    std::vector<float> fnorm;
    int numFiles = 0;
    float fieldNorm = 1.0f;
    int lastRnd = 0, lastLRnd = 0;

    // space (ObliqSonic)
    struct Pt { float fx, fy, fz, vx, vy, vz, lx, ly, lz, gx, gy, gz, qx, qy, qz, ox, oy, oz, wx, wy, wz, ds, dr, tx, ty, tz, x, y, z; };
    std::array<Pt, kPoints> pts;
    float spT = 0, wellT = 0, leadT = 0, yaw = 0, spAcc = 0;

    // midi for the current host buffer
    std::vector<std::pair<int, juce::MidiMessage>> events; size_t evPos = 0; int hostPos = 0;

    // cached parameter indices
    struct Ids;
    std::unique_ptr<Ids> id;
    std::vector<int> sIds, jSrc, jAtt, oG, lSrc, lDst, lAtt, oCvS, oCvA, scIds, ccnIds;
};
