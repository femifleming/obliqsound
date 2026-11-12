// ScEngine: scsynth (SuperCollider's synthesis server) embedded in-process, driven block by block
// by the host's audio callback. No audio device, no network: OSC goes in through World_SendPacket.
#pragma once
#include <atomic>
#include <cstdint>
#include <cstring>
#include <functional>
#include <string>
#include <vector>

struct World;
class ScEmbeddedDriver;

// Minimal OSC message writer (address, then int / float / string / blob arguments).
class OscMsg {
public:
    explicit OscMsg (const char* address) { str (addr, address); }
    OscMsg& i (int32_t v) { tags += 'i'; put32 ((uint32_t) v); return *this; }
    OscMsg& f (float v) { tags += 'f'; uint32_t u; std::memcpy (&u, &v, 4); put32 (u); return *this; }
    OscMsg& s (const char* v) { tags += 's'; str (data, v); return *this; }
    OscMsg& b (const void* p, int n) { tags += 'b'; put32 ((uint32_t) n); const char* c = (const char*) p; data.insert (data.end(), c, c + n); while (data.size() % 4) data.push_back (0); return *this; }
    std::vector<char> bytes() const
    {
        std::vector<char> out (addr);
        str (out, tags.c_str());
        out.insert (out.end(), data.begin(), data.end());
        return out;
    }
private:
    static void str (std::vector<char>& d, const char* v) { size_t n = std::strlen (v); d.insert (d.end(), v, v + n); d.push_back (0); while (d.size() % 4) d.push_back (0); }
    void put32 (uint32_t u) { char c[4] = { (char) (u >> 24), (char) (u >> 16), (char) (u >> 8), (char) u }; data.insert (data.end(), c, c + 4); }
    std::vector<char> addr, data; std::string tags = ",";
};

class ScEngine {
public:
    ScEngine();
    ~ScEngine();

    // pluginDir: folder of .scx UGen plug-ins. Returns false if the server could not be created.
    bool start (double sampleRate, int numOutputs, const std::string& pluginDir, int numBuffers = 128);
    void stop();
    bool isRunning() const { return world != nullptr; }

    // Thread-safe: queue an OSC message for the next audio block.
    void send (const OscMsg& m);
    // Load every .scsyndef in a folder / one definition from memory, and wait until the server has it.
    bool loadDefs (const std::string& dir);
    // Fill a server buffer directly (mono or interleaved), before or between notes. Not for the audio thread.
    bool setBuffer (int bufnum, int numChannels, int numFrames, double sampleRate, const float* interleaved);

    // Audio thread: render numFrames into outs[ch][0..numFrames).
    void process (float* const* outs, int numChannels, int numFrames);

    // Read a control bus (for meters and scopes); written by the audio thread once per block.
    float controlBus (int index) const;
    // Audio thread (or before audio starts): write a control bus directly, with no OSC message.
    void setControl (int index, float value);
    void setControls (int index, const float* values, int count);
    void pump (int blocks);                      // run blocks without a host (start-up, offline loading)
    // Called on the audio thread right before each 64-frame server block (argument: frames already rendered
    // in the current process() call). Write control buses and send note messages from here.
    std::function<void (int)> preBlock;
    double avgCpu() const;

private:
    void runBlock();
    World* world = nullptr;
    ScEmbeddedDriver* driver = nullptr;
    int nOut = 2;
    int64_t oscTime = 0, oscInc = 0;
    std::vector<std::vector<float>> block;       // one 64-frame server block per channel
    int blockPos = 64;                           // read position in the current block (64 = empty)
    std::atomic<int> doneCount { 0 };
    std::atomic<int> failCount { 0 };
    bool sync (int timeoutMs = 5000);            // wait until every queued asynchronous command is done
    static void replyFunc (struct ReplyAddress*, char* msg, int size);
};
