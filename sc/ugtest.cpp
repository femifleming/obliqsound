#include "ScEngine.h"
#include <chrono>
#include <cmath>
#include <cstdio>
int main (int, char** argv)
{
    for (const char* def : { "tfilt", "tpoly", "tadd", "tenc" })
    {
        const bool enc = std::string (def) == "tenc"; const int nch = enc ? 16 : 2;
        ScEngine e;
        if (! e.start (48000.0, nch, argv[1])) { std::puts ("start failed"); return 1; }
        if (! e.loadDefs (argv[2])) { std::puts ("defs failed"); return 1; }
        const int voices = enc ? 1 : 16;
        for (int i = 0; i < voices; ++i) e.send (OscMsg ("/s_new").s (def).i (1000 + i).i (0).i (0).s ("freq").f (enc ? 220.f : 55.0f * std::pow (2.0f, i * 3 / 12.0f)));
        std::vector<std::vector<float>> buf ((size_t) nch, std::vector<float> (512)); std::vector<float*> outs; for (auto& b : buf) outs.push_back (b.data());
        std::vector<double> sum ((size_t) nch, 0.0), dotW ((size_t) nch, 0.0); double peak = 0; bool finite = true; long n = 0;
        auto t0 = std::chrono::steady_clock::now();
        for (int b = 0; b < 48000 * 3 / 512; ++b)
        {
            e.process (outs.data(), nch, 512);
            for (int i = 0; i < 512; ++i) { for (int c = 0; c < nch; ++c) { float v = buf[(size_t) c][(size_t) i]; if (! std::isfinite (v)) finite = false; sum[(size_t) c] += v * v; dotW[(size_t) c] += v * buf[0][(size_t) i]; peak = std::max (peak, (double) std::fabs (v)); } ++n; }
        }
        double secs = std::chrono::duration<double> (std::chrono::steady_clock::now() - t0).count();
        std::printf ("%-6s x%-2d rms L %.4f R %.4f peak %.3f finite %d  cpu %.2f%% of real time\n", def, voices, std::sqrt (sum[0] / n), std::sqrt (sum[1] / n), peak, (int) finite, secs / 3 * 100);
        if (enc) { std::printf ("       channel / W:"); for (int c = 0; c < 16; ++c) std::printf (" %+.2f", dotW[(size_t) c] / dotW[0]); std::puts (""); }
        e.stop();
    }
    return 0;
}
