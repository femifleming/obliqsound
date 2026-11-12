// Spike: scsynth embedded in-process; play a chord, check the output and the cost.
#include "ScEngine.h"
#include <chrono>
#include <cmath>
#include <cstdio>
int main (int argc, char** argv)
{
    ScEngine e;
    if (! e.start (48000.0, 2, argv[1])) { std::puts ("start failed"); return 1; }
    std::printf ("defs loaded: %d\n", (int) e.loadDefs (argv[2]));
    for (int i = 0; i < 16; ++i) e.send (OscMsg ("/s_new").s ("spike").i (1000 + i).i (0).i (0).s ("freq").f (110.0f * std::pow (2.0f, i * 3 / 12.0f)).s ("amp").f (0.05f));
    std::vector<float> l (512), r (512); float* outs[2] = { l.data(), r.data() };
    double sum = 0, peak = 0; long n = 0;
    auto t0 = std::chrono::steady_clock::now();
    for (int b = 0; b < 48000 * 5 / 512; ++b)
    {
        e.process (outs, 2, 512);
        for (int i = 0; i < 512; ++i) { sum += l[i] * l[i]; peak = std::max (peak, (double) std::fabs (l[i])); ++n; }
    }
    double secs = std::chrono::duration<double> (std::chrono::steady_clock::now() - t0).count();
    std::printf ("16 voices, 5 s: rms %.4f peak %.4f, took %.3f s (%.1f%% of real time)\n", std::sqrt (sum / n), peak, secs, secs / 5 * 100);
    for (int i = 0; i < 16; ++i) e.send (OscMsg ("/n_set").i (1000 + i).s ("gate").f (0));
    for (int b = 0; b < 100; ++b) e.process (outs, 2, 512);
    e.stop(); std::puts ("stopped cleanly");
    return 0;
}
