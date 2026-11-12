#include "ScEngine.h"

#include "SC_CoreAudio.h"
#include "SC_HiddenWorld.h"
#include "SC_World.h"
#include "SC_WorldOptions.h"
#include "SC_ReplyImpl.hpp"

#include <chrono>
#include <thread>

// The server's audio driver with no device behind it: the host calls Run() one 64-frame block at a time.
class ScEmbeddedDriver : public SC_CoreAudioDriver {
public:
    ScEmbeddedDriver (World* w, double sr): SC_CoreAudioDriver (w), rate (sr) {}
    void render (AudioBufferList* out, int64 oscTime) { Run<false> (nullptr, out, oscTime); }
protected:
    bool DriverSetup (int* outNumSamples, double* outSampleRate) override { *outNumSamples = 64; *outSampleRate = rate; return true; }
    bool DriverStart() override { return true; }
    bool DriverStop() override { return true; }
private:
    double rate;
};

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
    AudioBufferList* abl = (AudioBufferList*) alloca (sizeof (AudioBufferList) + sizeof (AudioBuffer) * (size_t) nOut);
    abl->mNumberBuffers = (UInt32) nOut;
    for (int c = 0; c < nOut; ++c)
    {
        std::fill (block[(size_t) c].begin(), block[(size_t) c].end(), 0.0f);
        abl->mBuffers[c].mNumberChannels = 1;
        abl->mBuffers[c].mDataByteSize = 64 * sizeof (float);
        abl->mBuffers[c].mData = block[(size_t) c].data();
    }
    driver->render (abl, oscTime);
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

double ScEngine::avgCpu() const { return driver != nullptr ? driver->GetAvgCPU() : 0.0; }

void ScEngine::setControl (int index, float value)
{
    if (world != nullptr && index >= 0 && index < (int) world->mNumControlBusChannels) world->mControlBus[index] = value;
}

void ScEngine::setControls (int index, const float* values, int count)
{
    if (world != nullptr && index >= 0 && index + count <= (int) world->mNumControlBusChannels)
        std::memcpy (world->mControlBus + index, values, sizeof (float) * (size_t) count);
}
