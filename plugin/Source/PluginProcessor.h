#pragma once
#include "Engine.h"
#include <juce_audio_processors/juce_audio_processors.h>

#ifndef OBLIQ_SONIC
 #define OBLIQ_SONIC 0
#endif

class ObliqProcessor : public juce::AudioProcessor
{
public:
    ObliqProcessor();
    ~ObliqProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout&) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 4.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}
    void getStateInformation (juce::MemoryBlock&) override;
    void setStateInformation (const void*, int) override;

    static juce::File resourceDir();
    ParamStore params;
    juce::var layout;
    std::unique_ptr<Engine> engine;
    juce::MidiKeyboardState keyboard;                 // the standalone's computer keyboard feeds this

    // presets: factory (read-only, from the bundle) + the user's own
    juce::StringArray presetNames() const;
    void loadPreset (const juce::String& name);
    void savePreset (const juce::String& name);
    void removePreset (const juce::String& name);
    juce::String currentPreset { "Default" };
    std::atomic<int> presetVersion { 0 };
    // ObliqSonic: decode to a stereo pair (virtual cardioids at +-60 degrees). On in the desktop app, off in a DAW.
    std::atomic<bool> stereoMonitor { false };

private:
    void applyValues (const juce::var& obj);
    juce::var factory, user;
    juce::File userPresetFile() const;
    double preparedRate = 0;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ObliqProcessor)
};
