// Full-voice test: N voices (osc + polygon + additive + 4-pole filter) + master + a nature scene, buses written from C++.
#include "ScEngine.h"
#include <chrono>
#include <cmath>
#include <cstdio>
#include <algorithm>
#include <cstdlib>
#include <vector>
int main (int argc, char** argv)
{
    const int nOut = 2, base = nOut + 2, mix = base, dly = base + 2, rev = base + 4, field = base + 6, nat = base + 8, vb0 = base + 26;
    const int gb = 0, kb0 = 64, kn = 60;
    const int nv = argc > 3 ? std::atoi (argv[3]) : 16;
    const bool ode = argc > 4;
    ScEngine e;
    if (! e.start (48000.0, nOut, argv[1]) || ! e.loadDefs (argv[2])) { std::puts ("start/defs failed"); return 1; }
    e.send (OscMsg ("/g_new").i (10).i (0).i (0));                          // voices
    e.send (OscMsg ("/s_new").s ("oNat1").i (20).i (1).i (0).s ("natbus").i (nat));      // nature at the head
    e.send (OscMsg ("/s_new").s ("oFx").i (30).i (1).i (0).s ("gb").i (gb).s ("mix").i (mix).s ("dly").i (dly).s ("rev").i (rev).s ("fieldbus").i (field).s ("natbus").i (nat));
    float g[9] = { 0.25f, 0.14f, 0.375f, 0.35f, 0.126f, 0.5f, 3.0f, 0.3f, 0.0f };
    e.setControls (gb, g, 9);
    for (int v = 0; v < nv; ++v)
    {
        const int kb = kb0 + v * kn, vbus = vb0 + v * 2, grp = 100 + v;
        float k[60] = {};
        const float f = 55.0f * std::pow (2.0f, v * 3 / 12.0f);
        k[0] = f; k[1] = 0.5f; k[2] = 0.18f; k[3] = 0.3f; k[4] = 0.6f; k[5] = 2.0f; k[9] = 2.0f; k[11] = 0.1f; k[12] = 800.f; k[13] = 1.0f; k[14] = 0.5f;
        k[15] = 2000.f; k[16] = 0.3f; k[17] = 0.f; k[18] = 0.5f; k[19] = 6000.f; k[20] = 0.12f; k[21] = 0.f; k[22] = 0.5f; k[23] = 1.f; k[24] = 1.f; k[25] = 1.f; k[26] = 0.12f;
        k[27] = f; k[28] = 4.f; k[29] = 0.2f; k[31] = 1.f; k[32] = 0.2f; k[34] = 0.3f; k[35] = 0.7f;
        k[38] = f; k[39] = ode ? 0.5f : 0.f; k[40] = 64.f; k[41] = 0.5f; k[45] = 0.5f; k[47] = 0.8f; k[48] = 0.2f;
        e.setControls (kb, k, 60);
        e.send (OscMsg ("/g_new").i (grp).i (1).i (10));
        e.send (OscMsg ("/s_new").s ("ovOsc3").i (1000 + v * 8).i (1).i (grp).s ("kb").i (kb).s ("vbus").i (vbus).s ("uni").i (3).s ("natbus").i (nat));
        e.send (OscMsg ("/s_new").s ("ovPoly").i (1001 + v * 8).i (1).i (grp).s ("kb").i (kb).s ("vbus").i (vbus));
        if (ode) e.send (OscMsg ("/s_new").s ("ovOde1").i (1002 + v * 8).i (1).i (grp).s ("kb").i (kb).s ("vbus").i (vbus));
        e.send (OscMsg ("/s_new").s ("ovFilt4").i (1003 + v * 8).i (1).i (grp).s ("kb").i (kb).s ("vbus").i (vbus).s ("mix").i (mix).s ("dly").i (dly).s ("rev").i (rev));
    }
    std::vector<float> l (256), r (256); float* outs[2] = { l.data(), r.data() };
    double sum = 0, peak = 0, worst = 0; long n = 0; bool finite = true;
    auto t0 = std::chrono::steady_clock::now();
    for (int b = 0; b < 48000 * 6 / 256; ++b)
    {
        auto b0 = std::chrono::steady_clock::now();
        e.process (outs, 2, 256);
        worst = std::max (worst, std::chrono::duration<double, std::milli> (std::chrono::steady_clock::now() - b0).count());
        for (int i = 0; i < 256; ++i) { if (! std::isfinite (l[i])) finite = false; sum += l[i] * l[i]; peak = std::max (peak, (double) std::fabs (l[i])); ++n; }
    }
    double secs = std::chrono::duration<double> (std::chrono::steady_clock::now() - t0).count();
    std::printf ("%d voices%s: rms %.4f peak %.4f finite %d | %.1f%% of real time, worst 256-block %.2f ms (budget 5.33) | VU %.3f %.3f\n",
                 nv, ode ? " + additive" : "", std::sqrt (sum / n), peak, (int) finite, secs / 6 * 100, worst, e.controlBus (gb + 18), e.controlBus (gb + 19));
    e.stop();
    const bool ok = finite && std::sqrt (sum / n) > 0.005 && peak < 4.0;
    std::puts (ok ? "SMOKE TEST PASSED" : "SMOKE TEST FAILED");
    return ok ? 0 : 1;
}
