#include "PluginProcessor.h"
#include "PluginEditor.h"

namespace
{
    // a host-visible parameter backed by the store
    class StoreParam : public juce::AudioProcessorParameterWithID
    {
    public:
        StoreParam (ParamStore& s, int i) : AudioProcessorParameterWithID (juce::ParameterID (s.def (i).id, 1), s.def (i).id), store (s), index (i) {}
        float getValue() const override { return store.toNorm (index, store.get (index)); }
        void setValue (float v) override { store.set (index, store.fromNorm (index, v)); }
        float getDefaultValue() const override { return store.toNorm (index, store.def (index).def); }
        juce::String getText (float v, int) const override { return juce::String (store.fromNorm (index, v), 3); }
        float getValueForText (const juce::String& t) const override { return store.toNorm (index, t.getFloatValue()); }
        int getNumSteps() const override { const auto& d = store.def (index); return d.inc >= 1.0f ? (int) std::lrint ((d.hi - d.lo) / d.inc) + 1 : 0x7fffffff; }
    private:
        ParamStore& store; int index;
    };
}

juce::File ObliqProcessor::resourceDir()
{
    // macOS bundles and every VST3: <bundle>/Contents/<binary folder>/<binary>, resources in Contents/Resources.
    // The Windows and Linux desktop apps: a Resources folder beside the program.
    const auto exe = juce::File::getSpecialLocation (juce::File::currentExecutableFile);
    const auto inBundle = exe.getParentDirectory().getParentDirectory().getChildFile ("Resources");
    const auto beside = exe.getParentDirectory().getChildFile ("Resources");
    return (! inBundle.getChildFile ("layout.json").existsAsFile() && beside.getChildFile ("layout.json").existsAsFile()) ? beside : inBundle;
}

ObliqProcessor::ObliqProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", OBLIQ_SONIC ? juce::AudioChannelSet::ambisonic (3) : juce::AudioChannelSet::stereo(), true))
{
    layout = juce::JSON::parse (resourceDir().getChildFile ("layout.json"));
    if (auto* ws = layout["widgets"].getArray())
        for (auto& w : *ws)
        {
            const auto ch = w["channel"].toString(); const auto type = w["type"].toString();
            if (ch.isEmpty()) continue;
            ParamDef d; d.id = ch;
            const bool pin = ch.startsWithChar ('p') && ch.containsChar ('_') && w.hasProperty ("popup");
            if (auto* r = w["range"].getArray())
            {
                d.lo = (float) (double) (*r)[0]; d.hi = (float) (double) (*r)[1]; d.def = (float) (double) (*r)[2];
                d.skew = r->size() > 3 ? (float) (double) (*r)[3] : 1.0f; d.inc = r->size() > 4 ? (float) (double) (*r)[4] : 0.0f;
                d.automatable = ! pin;
            }
            else if (type == "checkbox") { d.lo = 0; d.hi = 1; d.inc = 1; d.def = (float) (double) w["value"]; d.automatable = ! ch.startsWith ("sc"); }
            else if (type == "button") { d.lo = 0; d.hi = 1000000; d.inc = 1; d.def = 0; }
            else if (type == "combobox" && w["text"].isArray() && ! w.hasProperty ("mode")) { d.lo = 1; d.hi = (float) w["text"].size(); d.inc = 1; d.def = w.hasProperty ("value") ? (float) (double) w["value"] : 1.0f; d.automatable = true; }
            else continue;
            params.add (d);
        }
    params.finish();
    for (int i = 0; i < params.size(); ++i)
        if (params.def (i).automatable) addParameter (new StoreParam (params, i));
    engine = std::make_unique<Engine> (params, OBLIQ_SONIC != 0, layout);
    factory = juce::JSON::parse (resourceDir().getChildFile ("presets.json"));
    user = juce::JSON::parse (userPresetFile());
    if (! user.isObject()) user = juce::var (new juce::DynamicObject());
    if (factory.hasProperty ("Default")) applyValues (factory["Default"]);
    stereoMonitor = OBLIQ_SONIC && wrapperType == wrapperType_Standalone;
}

ObliqProcessor::~ObliqProcessor() {}

bool ObliqProcessor::isBusesLayoutSupported (const BusesLayout& l) const
{
    const auto o = l.getMainOutputChannelSet();
    if (OBLIQ_SONIC) return o == juce::AudioChannelSet::ambisonic (3) || o == juce::AudioChannelSet::discreteChannels (16) || o.size() == 16;
    return o == juce::AudioChannelSet::stereo();
}

void ObliqProcessor::prepareToPlay (double sampleRate, int)
{
    if (preparedRate != sampleRate || ! engine->ready())
    {
        preparedRate = sampleRate;
        engine->prepare (sampleRate, resourceDir());
    }
}

void ObliqProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals nd;
    keyboard.processNextMidiBuffer (midi, 0, buffer.getNumSamples(), true);
    double bpm = 120.0;
    if (auto* ph = getPlayHead()) if (auto pos = ph->getPosition()) if (auto b = pos->getBpm()) bpm = *b;
    engine->process (buffer, midi, bpm);
    if (OBLIQ_SONIC && stereoMonitor.load() && buffer.getNumChannels() >= 4)
    {   // ACN / SN3D: W = 0, Y = 1, X = 3
        auto* w = buffer.getWritePointer (0); auto* y = buffer.getWritePointer (1); const auto* x = buffer.getReadPointer (3);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
        {
            const float l = 0.5f * (w[i] + 0.5f * x[i] + 0.866f * y[i]), r = 0.5f * (w[i] + 0.5f * x[i] - 0.866f * y[i]);
            w[i] = l; y[i] = r;
        }
        for (int c = 2; c < buffer.getNumChannels(); ++c) buffer.clear (c, 0, buffer.getNumSamples());
    }
}

juce::AudioProcessorEditor* ObliqProcessor::createEditor() { return new ObliqEditor (*this); }

// ---------------------------------------------------------------- state and presets
void ObliqProcessor::getStateInformation (juce::MemoryBlock& dest)
{
    juce::XmlElement xml ("ObliqState");
    xml.setAttribute ("preset", currentPreset);
    for (int i = 0; i < params.size(); ++i)
        if (params.get (i) != params.def (i).def && params.def (i).id != "rndAll")
            xml.createNewChildElement ("p")->setAttribute ("id", params.def (i).id), xml.getChildElement (xml.getNumChildElements() - 1)->setAttribute ("v", (double) params.get (i));
    copyXmlToBinary (xml, dest);
}

void ObliqProcessor::setStateInformation (const void* data, int size)
{
    if (auto xml = getXmlFromBinary (data, size))
    {
        if (! xml->hasTagName ("ObliqState")) return;
        const int rnd = params.find ("rndAll"); const float keep = params.get (rnd);
        params.resetAll();
        for (auto* e : xml->getChildIterator()) params.set (e->getStringAttribute ("id"), (float) e->getDoubleAttribute ("v"));
        params.set (rnd, keep);
        currentPreset = xml->getStringAttribute ("preset", "Default");
        ++presetVersion;
    }
}

juce::File ObliqProcessor::userPresetFile() const
{
    auto d = juce::File::getSpecialLocation (juce::File::userApplicationDataDirectory)
               #if JUCE_MAC
                .getChildFile ("Application Support")
               #endif
                .getChildFile (JucePlugin_Name);
    d.createDirectory();
    return d.getChildFile ("presets.json");
}

juce::StringArray ObliqProcessor::presetNames() const
{
    juce::StringArray n;
    if (auto* o = factory.getDynamicObject()) for (auto& p : o->getProperties()) n.add (p.name.toString());
    if (auto* o = user.getDynamicObject()) for (auto& p : o->getProperties()) n.addIfNotAlreadyThere (p.name.toString());
    n.sortNatural();
    if (n.contains ("Default")) { n.removeString ("Default"); n.insert (0, "Default"); }
    return n;
}

void ObliqProcessor::applyValues (const juce::var& obj)
{
    if (auto* o = obj.getDynamicObject())
    {
        const int rnd = params.find ("rndAll"); const float keep = params.get (rnd);
        // tabs and the window size are not part of a sound
        std::vector<std::pair<int, float>> hold;
        for (int i = 0; i < params.size(); ++i) if (params.def (i).id.startsWithChar ('t') && params.def (i).id.length() <= 6 && params.def (i).hi == 1.0f && params.def (i).id.substring (1, 2).toUpperCase() == params.def (i).id.substring (1, 2)) hold.push_back ({ i, params.get (i) });
        params.resetAll();
        for (auto& p : o->getProperties())
            if (p.value.isDouble() || p.value.isInt() || p.value.isInt64() || p.value.isBool()) params.set (p.name.toString(), (float) (double) p.value);
        for (auto& h : hold) params.set (h.first, h.second);
        params.set (rnd, keep);
    }
}

void ObliqProcessor::loadPreset (const juce::String& name)
{
    const juce::Identifier key (name);
    if (user.hasProperty (key)) applyValues (user[key]);
    else if (factory.hasProperty (key)) applyValues (factory[key]);
    else return;
    currentPreset = name; ++presetVersion;
}

void ObliqProcessor::savePreset (const juce::String& name)
{
    auto* o = new juce::DynamicObject();
    for (int i = 0; i < params.size(); ++i) if (params.def (i).id != "rndAll") o->setProperty (params.def (i).id, (double) params.get (i));
    user.getDynamicObject()->setProperty (juce::Identifier (name), juce::var (o));
    userPresetFile().replaceWithText (juce::JSON::toString (user));
    currentPreset = name; ++presetVersion;
}

void ObliqProcessor::removePreset (const juce::String& name)
{
    if (user.hasProperty (juce::Identifier (name))) { user.getDynamicObject()->removeProperty (juce::Identifier (name)); userPresetFile().replaceWithText (juce::JSON::toString (user)); ++presetVersion; }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new ObliqProcessor(); }
