#include "ScEngine.h"

#include "SC_CoreAudio.h"
#include "SC_HiddenWorld.h"
#include "SC_World.h"
#include "SC_WorldOptions.h"
#include "SC_ReplyImpl.hpp"
#include "SC_Prototypes.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <thread>

// The server's audio driver with no device behind it: the host calls render() one 64-frame block at a time.
// It derives from the server's generic driver class, so it is the same on macOS, Windows and Linux.
class ScEmbeddedDriver : public SC_AudioDriver {
public:
    ScEmbeddedDriver (World* w, double sr): SC_AudioDriver (w), rate (sr) {}
    // outs: one buffer of world->mBufLength frames per output bus, already cleared
    void render (float* const* outs, int numOuts, int64 oscTime)
    {
        const auto t0 = std::chrono::steady_clock::now();
        World* world = mWorld;
        try
        {
            mOSCbuftime = oscTime;
            mFromEngine.Free();
            mToEngine.Perform();
            mOscPacketsToEngine.Perform();
            const int bufFrames = world->mBufLength;
            const int32 bufCounter = world->mBufCounter;
            const int64 nextTime = oscTime + mOSCincrement;
            int64 schedTime;
            while ((schedTime = mScheduler.NextTime()) <= nextTime)
            {
                const float diffTime = (float) (schedTime - oscTime) * (float) mOSCtoSamples + 0.5f;
                const float diffFloor = std::floor (diffTime);
                world->mSampleOffset = std::min (std::max ((int) diffFloor, 0), bufFrames - 1);
                world->mSubsampleOffset = diffTime - diffFloor;
                SC_ScheduledEvent event = mScheduler.Remove();
                event.Perform();
            }
            world->mSampleOffset = 0;
            world->mSubsampleOffset = 0.0f;
            World_Run (world);
            const int n = std::min (numOuts, (int) world->mNumOutputs);
            for (int c = 0; c < n; ++c)
                if (world->mAudioBusTouched[c] == bufCounter)
                    std::memcpy (outs[c], world->mAudioBus + c * bufFrames, sizeof (float) * (size_t) bufFrames);
            mOSCbuftime = nextTime;
            world->mBufCounter++;
        }
        catch (...) {}
        mAudioSync.Signal();                  // wake the helper thread for whatever the block handed over
        const double secs = std::chrono::duration<double> (std::chrono::steady_clock::now() - t0).count();
        cpu += 0.1 * (secs * rate / 64.0 * 100.0 - cpu);
    }
    double cpu = 0.0;
protected:
    bool DriverSetup (int* outNumSamples, double* outSampleRate) override { *outNumSamples = 64; *outSampleRate = rate; return true; }
    bool DriverStart() override { return true; }
    bool DriverStop() override { return true; }
private:
    double rate;
};

#if ! defined (__APPLE__)
// On Windows and Linux the server's own device back end (PortAudio / JACK) is left out of the link;
// these are the few functions it would have provided.
#include "SC_Time.hpp"
extern "C" {
int32 server_timeseed() { return timeSeed(); }
int64 oscTimeNow() { return OSCTime (getTime()); }
}
void initializeScheduler() {}
SC_AudioDriver* SC_NewAudioDriver (struct World*) { return nullptr; }
#endif

ScEngine::ScEngine() {}
ScEngine::~ScEngine() { stop(); }

void ScEngine::replyFunc (ReplyAddress* addr, char* msg, int size)
{
    auto* self = static_cast<ScEngine*> (addr->mReplyData);
    if (self == nullptr || size < 8) return;
    if (std::strncmp (msg, "/synced", 7) == 0) self->doneCount++;
    else if (std::strncmp (msg, "/fail", 5) == 0) self->failCount++;
}

bool ScEngine::start (double sampleRate, int numOutputs, const std::string& pluginDir, int numBuffers)
{
    stop();
    nOut = numOutputs;
    WorldOptions o;
    o.mRealTime = false;                      // no audio device: we attach our own driver below
    o.mNumBuffers = (uint32) numBuffers;
    o.mMaxNodes = 4096;
    o.mMaxGraphDefs = 256;
    o.mMaxWireBufs = 1024;
    o.mNumAudioBusChannels = 256;
    o.mNumInputBusChannels = 2;
    o.mNumOutputBusChannels = (uint32) numOutputs;
    o.mNumControlBusChannels = 4096;
    o.mBufLength = 64;
    o.mRealTimeMemorySize = 131072;           // 128 MB for delay lines, grains and reverbs
    o.mLoadGraphDefs = 0;
    o.mVerbosity = -1;
    o.mRendezvous = false;
    o.mUGensPluginPath = pluginDir.c_str();
    o.mPreferredSampleRate = (uint32) sampleRate;
    world = World_New (&o);
    if (world == nullptr) return false;

    driver = new ScEmbeddedDriver (world, sampleRate);
    world->hw->mAudioDriver = driver;
    if (! driver->Setup() || ! driver->Start()) { stop(); return false; }
    world->mRealTime = true;                  // asynchronous commands now go through the driver's helper thread

    oscInc = (int64_t) ((double) world->mBufLength * 4294967296.0 / sampleRate);
    oscTime = oscTimeNow();
    block.assign ((size_t) nOut, std::vector<float> (64, 0.0f));
    blockPos = 64;
    return true;
}

void ScEngine::stop()
{
    if (world != nullptr)
    {
        World_Cleanup (world, false);          // deletes the driver too
        world = nullptr; driver = nullptr;
    }
}

void ScEngine::send (const OscMsg& m)
{
    if (world == nullptr) return;
    auto b = m.bytes();
    World_SendPacketWithContext (world, (int) b.size(), b.data(), &ScEngine::replyFunc, this);
}

void ScEngine::runBlock()
{
    float* outs[64];
    const int n = std::min (nOut, 64);
    for (int c = 0; c < n; ++c) { std::fill (block[(size_t) c].begin(), block[(size_t) c].end(), 0.0f); outs[c] = block[(size_t) c].data(); }
    driver->render (outs, n, oscTime);
    oscTime += oscInc;
}

void ScEngine::process (float* const* outs, int numChannels, int numFrames)
{
    if (world == nullptr) { for (int c = 0; c < numChannels; ++c) std::fill (outs[c], outs[c] + numFrames, 0.0f); return; }
    int done = 0;
    while (done < numFrames)
    {
        if (blockPos >= 64) { if (preBlock) preBlock (done); runBlock(); blockPos = 0; }
        const int n = std::min (64 - blockPos, numFrames - done);
        for (int c = 0; c < numChannels; ++c)
        {
            if (c < nOut) std::memcpy (outs[c] + done, block[(size_t) c].data() + blockPos, sizeof (float) * (size_t) n);
            else std::fill (outs[c] + done, outs[c] + done + n, 0.0f);
        }
        blockPos += n; done += n;
    }
}

void ScEngine::pump (int blocks) { for (int i = 0; i < blocks && world != nullptr; ++i) runBlock(); }

bool ScEngine::sync (int timeoutMs)
{
    const int before = doneCount.load();
    send (OscMsg ("/sync").i (1));
    for (int waited = 0; waited < timeoutMs; waited += 2)
    {
        pump (1);                                                    // let the engine hand work to its helper thread
        if (doneCount.load() != before) return true;
        std::this_thread::sleep_for (std::chrono::milliseconds (2));
    }
    return false;
}

bool ScEngine::loadDefs (const std::string& dir)
{
    const int fails = failCount.load();
    send (OscMsg ("/d_loadDir").s (dir.c_str()));
    return sync() && failCount.load() == fails;
}

bool ScEngine::setBuffer (int bufnum, int numChannels, int numFrames, double sampleRate, const float* interleaved)
{
    if (world == nullptr || bufnum < 0 || bufnum >= (int) world->mNumSndBufs) return false;
    send (OscMsg ("/b_alloc").i (bufnum).i (numFrames).i (numChannels));
    if (! sync()) return false;
    SndBuf* b = world->mSndBufs + bufnum;
    if (b->data == nullptr || b->samples < numFrames * numChannels) return false;
    std::memcpy (b->data, interleaved, sizeof (float) * (size_t) (numFrames * numChannels));
    b->samplerate = sampleRate; b->sampledur = 1.0 / sampleRate;
    SndBuf* m = world->mSndBufsNonRealTimeMirror + bufnum;
    m->samplerate = sampleRate; m->sampledur = 1.0 / sampleRate;
    return true;
}

float ScEngine::controlBus (int index) const
{
    return (world != nullptr && index >= 0 && index < (int) world->mNumControlBusChannels) ? world->mControlBus[index] : 0.0f;
}

double ScEngine::avgCpu() const { return driver != nullptr ? driver->cpu : 0.0; }

void ScEngine::setControl (int index, float value)
{
    if (world != nullptr && index >= 0 && index < (int) world->mNumControlBusChannels) world->mControlBus[index] = value;
}

void ScEngine::setControls (int index, const float* values, int count)
{
    if (world != nullptr && index >= 0 && index + count <= (int) world->mNumControlBusChannels)
        std::memcpy (world->mControlBus + index, values, sizeof (float) * (size_t) count);
}
