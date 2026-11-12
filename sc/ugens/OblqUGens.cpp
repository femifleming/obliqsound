// OblqUGens: the signature DSP of ObliqSound / ObliqSonic as SuperCollider UGens.
//   OblqFilter  - gain/overdrive into a zero-delay 2-pole state-variable filter whose mode morphs
//                 LP > BP > HP > notch > comb (after the Bionic Lester). Cutoff is smoothed per sample.
//   OblqPoly    - polygonal oscillator traced in X/Y (after the Polygogo), 2x oversampled.
//   OblqAdd     - additive bank of up to 128 partials in two banks (after the Odessa):
//                 tilt, tension, density comb with warp and peaking, bank split, factor, group gates.
//   OblqEncode  - third-order Ambisonics point encoder (ACN / SN3D, 16 outputs) with distance:
//                 propagation delay (Doppler), 1/r, air absorption, near-field spread.
#include "SC_PlugIn.h"
#include <cmath>
#include <cstring>

static InterfaceTable* ft;

static inline float clampf (float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
static const double kTwoPi = 6.283185307179586;

// =====================================================================================  OblqFilter
struct OblqFilter : public Unit
{
    float ic1, ic2;          // SVF state
    float fc;                // smoothed cutoff (Hz)
    float res, mode, gain;   // smoothed controls
    float* dl; int dlMask, dlPos; float combLp;
};

static void OblqFilter_next (OblqFilter* unit, int n)
{
    const float* in = IN (0);
    float* out = OUT (0);
    const float sr = (float) SAMPLERATE;
    const float fcT = clampf (IN0 (1), 20.f, sr * 0.45f);
    const float resT = clampf (IN0 (2), 0.f, 1.f), modeT = clampf (IN0 (3), 0.f, 4.f), gainT = clampf (IN0 (4), 0.f, 1.f);
    float fc = unit->fc, res = unit->res, mode = unit->mode, gain = unit->gain;
    const float inv = 1.f / (float) n;
    const float dfc = (fcT - fc) * inv, dres = (resT - res) * inv, dmode = (modeT - mode) * inv, dgain = (gainT - gain) * inv;
    float ic1 = unit->ic1, ic2 = unit->ic2;
    const float piOverSr = 3.14159265f / sr;

    for (int i = 0; i < n; ++i)
    {
        fc += dfc; res += dres; mode += dmode; gain += dgain;
        // ---- gain / overdrive: clean to noon, then soft into hard clipping
        float x = in[i];
        if (gain <= 0.5f) x *= gain * 2.f;
        else
        {
            const float d = (gain - 0.5f) * 2.f;
            const float soft = std::tanh (x * (1.f + d * 5.f));
            const float hard = clampf (x * (1.f + d * 10.f), -0.8f, 0.8f) * 1.25f;
            const float h = d * d * d;
            x = soft * (1.f - h) + hard * h;
        }
        // ---- zero-delay state-variable filter (trapezoidal)
        const float q = 0.6f + res * res * 11.f;
        const float k = 1.f / q;
        const float g = std::tan (piOverSr * fc);
        const float a1 = 1.f / (1.f + g * (g + k));
        const float a2 = g * a1, a3 = g * a2;
        const float v3 = x - ic2;
        const float v1 = a1 * ic1 + a2 * v3;
        const float v2 = ic2 + a2 * ic1 + a3 * v3;
        ic1 = 2.f * v1 - ic1; ic2 = 2.f * v2 - ic2;
        const float lp = v2, bp = v1 * k, hp = x - k * v1 - v2, notch = lp + hp;
        // ---- morph
        float y;
        if (mode < 1.f) y = lp + (bp - lp) * mode;
        else if (mode < 2.f) y = bp + (hp - bp) * (mode - 1.f);
        else if (mode < 3.f) y = hp + (notch - hp) * (mode - 2.f);
        else
        {   // comb: resonance 0 = allpass-ish, to noon = +comb, past noon = -comb
            const float fb = (res < 0.5f ? res * 2.f : -(res - 0.5f) * 2.f) * 0.96f;
            const float delay = sr / fc;                              // in samples
            float rp = (float) unit->dlPos - delay; while (rp < 0.f) rp += (float) (unit->dlMask + 1);
            const int i0 = (int) rp; const float fr = rp - (float) i0;
            const float d0 = unit->dl[i0 & unit->dlMask], d1 = unit->dl[(i0 + 1) & unit->dlMask];
            const float del = d0 + (d1 - d0) * fr;
            unit->dl[unit->dlPos & unit->dlMask] = x + fb * del;
            const float comb = del * (1.f - std::fabs (fb) * 0.6f);
            y = notch + (comb - notch) * (mode - 3.f);
        }
        if (mode < 3.f) unit->dl[unit->dlPos & unit->dlMask] = x;              // keep the comb line primed
        unit->dlPos = (unit->dlPos + 1) & unit->dlMask;
        out[i] = zapgremlins (y / (1.f + res * 1.2f + res * res * 2.5f));
    }
    unit->ic1 = zapgremlins (ic1); unit->ic2 = zapgremlins (ic2);
    unit->fc = fcT; unit->res = resT; unit->mode = modeT; unit->gain = gainT;
}

static void OblqFilter_Ctor (OblqFilter* unit)
{
    unit->ic1 = unit->ic2 = 0.f; unit->combLp = 0.f;
    unit->fc = clampf (IN0 (1), 20.f, (float) SAMPLERATE * 0.45f);
    unit->res = IN0 (2); unit->mode = IN0 (3); unit->gain = IN0 (4);
    int size = 1; while (size < (int) (SAMPLERATE / 20.0) + 4) size <<= 1;
    unit->dl = (float*) RTAlloc (unit->mWorld, sizeof (float) * (size_t) size);
    if (unit->dl == nullptr) { SETCALC (ft->fClearUnitOutputs); ClearUnitOutputs (unit, 1); return; }
    std::memset (unit->dl, 0, sizeof (float) * (size_t) size);
    unit->dlMask = size - 1; unit->dlPos = 0;
    SETCALC (OblqFilter_next);
    OblqFilter_next (unit, 1);
}
static void OblqFilter_Dtor (OblqFilter* unit) { if (unit->dl) RTFree (unit->mWorld, unit->dl); }

// =====================================================================================  OblqPoly
struct OblqPoly : public Unit
{
    double ph, op, pr;       // main, operator and precession phases (cycles)
    float order, teeth, roll, amt, skew;
};

static inline void polyPoint (double ph, double op, double pr, float order, float teeth, float roll, float amt, float skew, bool cycle,
                              float& X, float& Y)
{
    const double th = ph + amt * std::sin (kTwoPi * op) * 0.3;
    const double nn = order < 2.05f ? 2.05 : (order > 32.f ? 32.0 : order);
    const double pin = M_PI / nn;
    double tmax = M_PI / 2 - pin - 0.07; if (tmax < 0) tmax = 0;
    const double T = teeth * tmax;
    double fr = th * nn; fr -= std::floor (fr);
    double den = std::cos (2 * pin * fr - pin + T); if (den < 0.04) den = 0.04; if (den > 1) den = 1;
    const double P = std::cos (pin + T) / den;
    double ang = kTwoPi * (th + roll);
    if (cycle) ang += kTwoPi * pr;
    X = (float) (P * std::cos (ang));
    Y = (float) (P * std::sin (ang + skew * M_PI * 0.5));
}

static void OblqPoly_next (OblqPoly* unit, int n)
{
    float* outX = OUT (0); float* outY = OUT (1);
    const bool arFreq = INRATE (0) == calc_FullRate;
    const float* fin = IN (0);
    const float orderT = IN0 (1), teethT = clampf (IN0 (2), 0.f, 1.f), rollT = IN0 (3);
    const float ratio = IN0 (4), amtT = clampf (IN0 (5), 0.f, 1.f), skewT = IN0 (7);
    const bool cycle = IN0 (6) > 0.5f;
    const float inv = 1.f / (float) n;
    float order = unit->order, teeth = unit->teeth, roll = unit->roll, amt = unit->amt, skew = unit->skew;
    const float dOrder = (orderT - order) * inv, dTeeth = (teethT - teeth) * inv, dRoll = (rollT - roll) * inv, dAmt = (amtT - amt) * inv, dSkew = (skewT - skew) * inv;
    double ph = unit->ph, op = unit->op, pr = unit->pr;
    const double half = 0.5 / SAMPLERATE;                       // 2x oversampling: two points per output sample
    const float nyq = (float) SAMPLERATE * 0.45f;

    for (int i = 0; i < n; ++i)
    {
        order += dOrder; teeth += dTeeth; roll += dRoll; amt += dAmt; skew += dSkew;
        const float f = clampf (arFreq ? fin[i] : fin[0], 0.f, nyq);
        float x0, y0, x1, y1;
        const double inc = f * half;
        polyPoint (ph, op, pr, order, teeth, roll, amt, skew, cycle, x0, y0);
        ph += inc; op += inc * ratio; pr += inc / (order < 2.05f ? 2.05f : order);
        polyPoint (ph, op, pr, order, teeth, roll, amt, skew, cycle, x1, y1);
        ph += inc; op += inc * ratio; pr += inc / (order < 2.05f ? 2.05f : order);
        ph -= std::floor (ph); op -= std::floor (op); pr -= std::floor (pr);
        outX[i] = 0.5f * (x0 + x1); outY[i] = 0.5f * (y0 + y1);
    }
    unit->ph = ph; unit->op = op; unit->pr = pr;
    unit->order = orderT; unit->teeth = teethT; unit->roll = rollT; unit->amt = amtT; unit->skew = skewT;
}

static void OblqPoly_Ctor (OblqPoly* unit)
{
    unit->ph = unit->op = unit->pr = 0.0;
    unit->order = IN0 (1); unit->teeth = IN0 (2); unit->roll = IN0 (3); unit->amt = IN0 (5); unit->skew = IN0 (7);
    SETCALC (OblqPoly_next);
    OblqPoly_next (unit, 1);
}

// =====================================================================================  OblqAdd
// inputs: 0 freq, 1 partials, 2 tilt, 3 tension, 4 density, 5 warp, 6 peaking, 7 bank, 8 factor, 9 gate mask (0..255)
struct OblqAdd : public Unit
{
    enum { kMax = 128 };
    double phA[kMax], phB[kMax];
    float ampA[kMax], ampB[kMax];
    float norm;
};

static void OblqAdd_next (OblqAdd* unit, int n)
{
    float* outA = OUT (0); float* outB = OUT (1);
    const double sr = SAMPLERATE;
    const float freq = clampf (IN0 (0), 1.f, (float) sr * 0.45f);
    const float partials = clampf (IN0 (1), 1.f, (float) OblqAdd::kMax);
    const float tilt = clampf (IN0 (2), 0.f, 1.f);
    float ten = clampf (IN0 (3), -1.f, 1.f);
    ten = ten > 0.04f ? (ten - 0.04f) / 0.96f : (ten < -0.04f ? (ten + 0.04f) / 0.96f : 0.f);
    const float dens = clampf (IN0 (4), 0.f, 1.f), warp = clampf (IN0 (5), 0.f, 1.f), peak = clampf (IN0 (6), 0.f, 1.f);
    const int bank = (int) std::lrint (IN0 (7)); const int L = std::abs (bank), Lg = L < 1 ? 1 : L;
    const int fi = (int) std::lrint (IN0 (8));
    const float fac = fi >= 0 ? (float) (fi + 1) : 1.f / (float) (1 - fi);
    const int mask = (int) IN0 (9);
    const float gam = 3.f * std::pow (1.f - tilt, 1.585f);
    const float qx = 0.15f * std::pow (30.f, peak);
    const float P = dens > 0.001f ? 2.f / dens : 0.f;
    const float a = 1.f / (1.f + 3.f * warp);
    const float c512 = std::pow (512.f, 1.f - a);
    const double nyq = sr * 0.45 / freq;
    const int count = (int) std::ceil (partials);

    std::memset (outA, 0, sizeof (float) * (size_t) n);
    std::memset (outB, 0, sizeof (float) * (size_t) n);
    float sum = 0.f;
    float tA[OblqAdd::kMax], tB[OblqAdd::kMax]; double rA[OblqAdd::kMax], rB[OblqAdd::kMax];

    for (int p = 1; p <= count; ++p)
    {
        double r = 1.0;
        if (p > 1) { r = std::fabs (1.0 + (p - 1) * (1.0 + ten * 0.06 * (p - 1))); if (r < 0.05) r = 0.05; }
        float comb = 1.f;
        if (P > 0.f) { const float ar = 3.14159265f * c512 * std::pow ((float) r, a) / P; comb = std::pow (std::fabs (std::sin (ar) / ar), qx); }
        float amp = std::pow ((float) p, -gam) * comb;
        if ((float) p > partials) amp *= clampf (1.f - ((float) p - partials), 0.f, 1.f);
        float inA = 1.f, inB = 1.f; double ra = r, rb = r;
        if (p >= 2)
        {
            int gi = (p - 2) / Lg; if (gi > 7) gi = 7;
            if (((mask >> gi) & 1) == 0) amp = 0.f;
            if (L > 0) { const int par = ((p - 2) / L) % 2; inA = (float) par; inB = (float) (1 - par); }
            if (bank >= 0) rb = r * fac; else ra = r * fac;
        }
        tA[p - 1] = ra < nyq ? amp * inA : 0.f;
        tB[p - 1] = rb < nyq ? amp * inB : 0.f;
        rA[p - 1] = ra; rB[p - 1] = rb;
        sum += tA[p - 1] * tA[p - 1] + (L > 0 ? tB[p - 1] * tB[p - 1] : 0.f);
    }
    const float normT = 1.f / std::sqrt (sum > 1e-6f ? sum : 1e-6f);
    const float norm0 = unit->norm, dnorm = (normT - norm0) / (float) n;
    const double w0 = kTwoPi * freq / sr;

    // one resonator per partial: y[n] = 2 cos(w) y[n-1] - y[n-2], re-seeded from its phase every block
    auto runBank = [&] (double* ph, float* amps, const float* target, const double* ratio, float* out, int np)
    {
        for (int p = 0; p < np; ++p)
        {
            const float a0 = amps[p], a1 = target[p];
            const double w = w0 * ratio[p];
            if (a0 > 1e-6f || a1 > 1e-6f)
            {
                const double c2 = 2.0 * std::cos (w);
                double y1 = std::sin (ph[p] - w), y0 = std::sin (ph[p]);   // y[-1], y[0]
                float amp = a0; const float da = (a1 - a0) / (float) n;
                for (int i = 0; i < n; ++i)
                {
                    out[i] += (float) y0 * amp; amp += da;
                    const double y2 = c2 * y0 - y1; y1 = y0; y0 = y2;
                }
            }
            ph[p] = std::fmod (ph[p] + w * n, kTwoPi);
            amps[p] = a1;
        }
        for (int p = np; p < OblqAdd::kMax; ++p) amps[p] = 0.f;
    };
    runBank (unit->phA, unit->ampA, tA, rA, outA, count);
    if (L > 0) runBank (unit->phB, unit->ampB, tB, rB, outB, count);

    float nm = norm0;
    if (L > 0) for (int i = 0; i < n; ++i) { nm += dnorm; outA[i] *= nm; outB[i] *= nm; }
    else for (int i = 0; i < n; ++i) { nm += dnorm; outA[i] *= nm; outB[i] = outA[i]; }
    unit->norm = normT;
}

static void OblqAdd_Ctor (OblqAdd* unit)
{
    RGen& rg = *unit->mParent->mRGen;
    for (int p = 0; p < OblqAdd::kMax; ++p) { unit->phA[p] = rg.frand() * kTwoPi; unit->phB[p] = rg.frand() * kTwoPi; unit->ampA[p] = unit->ampB[p] = 0.f; }
    unit->norm = 0.f;
    SETCALC (OblqAdd_next);
    OblqAdd_next (unit, 1);
}

// =====================================================================================  OblqEncode
// inputs: 0 in, 1 x, 2 y, 3 z (metres; x front, y left, z up), 4 spread, 5 air, 6 doppler, 7 reference distance
// outputs: 16 channels, ACN order, SN3D
struct OblqEncode : public Unit
{
    float* dl; int dlMask, dlPos;
    float x, y, z, lp;
    float g[16];
    bool first;
};

static void shGains (float x, float y, float z, float w1, float w2, float w3, float* g)
{
    const float x2 = x * x, y2 = y * y, z2 = z * z;
    g[0] = 1.f;
    g[1] = y * w1; g[2] = z * w1; g[3] = x * w1;
    g[4] = 1.7320508f * x * y * w2; g[5] = 1.7320508f * y * z * w2; g[6] = 0.5f * (3.f * z2 - 1.f) * w2;
    g[7] = 1.7320508f * x * z * w2; g[8] = 0.8660254f * (x2 - y2) * w2;
    g[9] = 0.7905694f * y * (3.f * x2 - y2) * w3; g[10] = 3.8729833f * x * y * z * w3; g[11] = 0.6123724f * y * (5.f * z2 - 1.f) * w3;
    g[12] = 0.5f * z * (5.f * z2 - 3.f) * w3; g[13] = 0.6123724f * x * (5.f * z2 - 1.f) * w3; g[14] = 1.9364917f * z * (x2 - y2) * w3;
    g[15] = 0.7905694f * x * (x2 - 3.f * y2) * w3;
}

static void OblqEncode_next (OblqEncode* unit, int n)
{
    const float* in = IN (0);
    const float sr = (float) SAMPLERATE;
    const float xT = IN0 (1), yT = IN0 (2), zT = IN0 (3);
    const float spread = clampf (IN0 (4), 0.f, 1.f), air = clampf (IN0 (5), 0.f, 1.f), dopp = clampf (IN0 (6), 0.f, 1.f);
    const float ref = IN0 (7) < 0.1f ? 0.1f : IN0 (7);
    const float inv = 1.f / (float) n;
    // distance at the start and end of the block (the delay glides, which is the Doppler shift)
    const float r0 = std::sqrt (unit->x * unit->x + unit->y * unit->y + unit->z * unit->z) + 1e-4f;
    const float r1 = std::sqrt (xT * xT + yT * yT + zT * zT) + 1e-4f;
    const float d0 = (r0 > 30.f ? 30.f : r0) / 343.f * sr * dopp, d1 = (r1 > 30.f ? 30.f : r1) / 343.f * sr * dopp;
    // target gains at the end of the block
    const float near = r1 > 1.f ? 1.f : r1;
    const float w = near * (1.f - spread);
    float gT[16]; shGains (xT / r1, yT / r1, zT / r1, w, w * w, w * w * w, gT);
    float gain = ref / (r1 < 0.5f ? 0.5f : r1); if (gain > 2.f) gain = 2.f;
    for (int c = 0; c < 16; ++c) gT[c] *= gain;
    if (unit->first) { std::memcpy (unit->g, gT, sizeof (gT)); unit->first = false; }
    const float cut = 20000.f * std::exp (-(r1 > 40.f ? 40.f : r1) * air * 0.12f);
    const float lc = 1.f - std::exp (-6.2831853f * (cut > sr * 0.45f ? sr * 0.45f : cut) / sr);

    float tmp[512];                                    // server blocks are 64 frames
    float lp = unit->lp, d = d0; const float dd = (d1 - d0) * inv;
    for (int i = 0; i < n && i < 512; ++i)
    {
        unit->dl[unit->dlPos & unit->dlMask] = in[i];
        d += dd;
        float rp = (float) unit->dlPos - d; if (rp < 0.f) rp += (float) (unit->dlMask + 1);
        const int i0 = (int) rp; const float fr = rp - (float) i0;
        const float a = unit->dl[i0 & unit->dlMask], b = unit->dl[(i0 + 1) & unit->dlMask];
        lp += lc * ((a + (b - a) * fr) - lp);
        tmp[i] = lp;
        unit->dlPos = (unit->dlPos + 1) & unit->dlMask;
    }
    unit->lp = zapgremlins (lp);
    for (int c = 0; c < 16; ++c)
    {
        float* out = OUT (c);
        float g = unit->g[c]; const float dg = (gT[c] - g) * inv;
        for (int i = 0; i < n; ++i) { g += dg; out[i] = tmp[i] * g; }
        unit->g[c] = gT[c];
    }
    unit->x = xT; unit->y = yT; unit->z = zT;
}

static void OblqEncode_Ctor (OblqEncode* unit)
{
    int size = 1; while (size < (int) (SAMPLERATE * 30.0 / 343.0) + 8) size <<= 1;
    unit->dl = (float*) RTAlloc (unit->mWorld, sizeof (float) * (size_t) size);
    if (unit->dl == nullptr) { SETCALC (ft->fClearUnitOutputs); ClearUnitOutputs (unit, 1); return; }
    std::memset (unit->dl, 0, sizeof (float) * (size_t) size);
    unit->dlMask = size - 1; unit->dlPos = 0; unit->lp = 0.f; unit->first = true;
    unit->x = IN0 (1); unit->y = IN0 (2); unit->z = IN0 (3);
    SETCALC (OblqEncode_next);
    OblqEncode_next (unit, 1);
}
static void OblqEncode_Dtor (OblqEncode* unit) { if (unit->dl) RTFree (unit->mWorld, unit->dl); }

PluginLoad (Oblq)
{
    ft = inTable;
    DefineDtorUnit (OblqFilter);
    DefineSimpleUnit (OblqPoly);
    DefineSimpleUnit (OblqAdd);
    DefineDtorUnit (OblqEncode);
}
