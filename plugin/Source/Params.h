// Parameter store: every channel of the panel (knobs, switches, lists, matrix pins) by name.
// Values are atomics, so the audio thread, the editor and the host can all read and write them.
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include <memory>
#include <unordered_map>
#include <vector>

struct ParamDef
{
    juce::String id;
    float lo = 0, hi = 1, def = 0, skew = 1, inc = 0;
    bool automatable = false;
};

class ParamStore
{
public:
    void add (const ParamDef& d)
    {
        if (index.count (d.id.toStdString())) return;
        index[d.id.toStdString()] = (int) defs.size();
        defs.push_back (d);
    }
    void finish()
    {
        vals = std::make_unique<std::atomic<float>[]> (defs.size());
        for (size_t i = 0; i < defs.size(); ++i) vals[i] = defs[i].def;
    }
    int find (const juce::String& id) const { auto it = index.find (id.toStdString()); return it == index.end() ? -1 : it->second; }
    int size() const { return (int) defs.size(); }
    const ParamDef& def (int i) const { return defs[(size_t) i]; }
    float get (int i) const { return i >= 0 ? vals[(size_t) i].load (std::memory_order_relaxed) : 0.0f; }
    float get (const juce::String& id) const { return get (find (id)); }
    void set (int i, float v)
    {
        if (i < 0) return;
        const auto& d = defs[(size_t) i];
        vals[(size_t) i].store (juce::jlimit (juce::jmin (d.lo, d.hi), juce::jmax (d.lo, d.hi), v), std::memory_order_relaxed);
        ++changeCount;
    }
    void set (const juce::String& id, float v) { set (find (id), v); }
    void resetAll() { for (size_t i = 0; i < defs.size(); ++i) vals[i] = defs[i].def; ++changeCount; }

    // normalised 0..1 <-> value, with the panel's skew (as JUCE's NormalisableRange does it)
    float toNorm (int i, float v) const
    {
        const auto& d = defs[(size_t) i];
        if (d.hi == d.lo) return 0.0f;
        const float p = juce::jlimit (0.0f, 1.0f, (v - d.lo) / (d.hi - d.lo));
        return d.skew == 1.0f ? p : std::pow (p, d.skew);
    }
    float fromNorm (int i, float n) const
    {
        const auto& d = defs[(size_t) i];
        n = juce::jlimit (0.0f, 1.0f, n);
        if (d.skew != 1.0f && n > 0.0f) n = std::pow (n, 1.0f / d.skew);
        float v = d.lo + (d.hi - d.lo) * n;
        if (d.inc > 0.0f) v = d.lo + std::round ((v - d.lo) / d.inc) * d.inc;
        return v;
    }
    std::atomic<int> changeCount { 0 };       // bumped on every write: the editor and the engine watch it

private:
    std::vector<ParamDef> defs;
    std::unique_ptr<std::atomic<float>[]> vals;
    std::unordered_map<std::string, int> index;
};
