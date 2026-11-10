// Headless VST3 host for testing ObliqSound / ObliqSonic.
// usage: ObliqHost <plugin.vst3> [--list] [--snap out.png] [--wav out.wav] [--secs N]
//                [--set name=norm ...] [--settext name=text ...]
//                [--notes "note:start:dur:vel,..."] [--wait ms]
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_gui_extra/juce_gui_extra.h>
#import <AppKit/AppKit.h>

using namespace juce;

static AudioProcessorParameter* findParam (AudioPluginInstance& p, const String& name)
{
    for (auto* prm : p.getParameters())
        if (prm->getName (128) == name) return prm;
    return nullptr;
}

class App : public JUCEApplication
{
public:
    const String getApplicationName() override { return "ObliqHost"; }
    const String getApplicationVersion() override { return "1"; }

    void initialise (const String&) override
    {
        auto args = getCommandLineParameterArray();
        int rc = run (args);
        setApplicationReturnValue (rc);
        quit();
    }
    void shutdown() override {}

    int run (const StringArray& args)
    {
        if (args.isEmpty()) { std::puts ("need plugin path"); return 1; }
        AudioPluginFormatManager fm;
        addDefaultFormatsToManager (fm);
        OwnedArray<PluginDescription> descs;
        VST3PluginFormat vst3;
        vst3.findAllTypesForFile (descs, args[0]);
        if (descs.isEmpty()) { std::puts ("no plugin found"); return 1; }
        auto& d = *descs[0];
        std::printf ("name=%s uid=%08x id=%s mfr=%s\n", d.name.toRawUTF8(), d.uniqueId,
                     d.createIdentifierString().toRawUTF8(), d.manufacturerName.toRawUTF8());

        const double sr = 48000; const int block = 512;
        String err;
        auto inst = fm.createPluginInstance (d, sr, block, err);
        if (! inst) { std::printf ("create failed: %s\n", err.toRawUTF8()); return 1; }
        std::printf ("buses out=%d in=%d totalOut=%d mainOut=%d\n", inst->getBusCount (false), inst->getBusCount (true), inst->getTotalNumOutputChannels(), inst->getBusCount (false) ? inst->getBus (false, 0)->getNumberOfChannels() : 0);
        if (inst->getBusCount (false)) { auto* b = inst->getBus (false, 0); for (int n : {2, 16, 36, 64}) std::printf ("  %d ch supported: %d\n", n, (int) b->isLayoutSupported (AudioChannelSet::discreteChannels (n))); }
        if (inst->getTotalNumOutputChannels() > 2) { if (std::getenv ("KH_ENABLEBUSES")) inst->enableAllBuses(); inst->setRateAndBufferSizeDetails (sr, block); } else inst->setPlayConfigDetails (0, 2, sr, block);
        inst->prepareToPlay (sr, block);
        {   // let Cabbage finish its start-up resets before touching parameters
            AudioBuffer<float> wb (2, block); auto end = Time::getMillisecondCounter() + 1500;
            while (Time::getMillisecondCounter() < end) { wb.clear(); MidiBuffer mm; inst->processBlock (wb, mm);
                MessageManager::getInstance()->runDispatchLoopUntil (5); }
        }

        double secs = 4; String wavPath, snapPath; int waitMs = 300; bool realtime = false, withEditor = false; std::vector<std::pair<String,float>> guiSets; Array<juce::Point<int>> clicks; Array<int> holds;
        Array<std::tuple<int,double,double,int>> notes;
        Array<std::tuple<int,double,int,int>> ccs;   // cc:time:value:channel
        for (int i = 1; i < args.size(); ++i)
        {
            const auto& a = args[i];
            if (a == "--list")
            {
                int idx = 0;
                for (auto* prm : inst->getParameters())
                    std::printf ("%3d %-22s val=%.4f text=%s\n", idx++, prm->getName (64).toRawUTF8(),
                                 prm->getValue(), prm->getCurrentValueAsText().toRawUTF8());
            }
            else if (a == "--secs") secs = args[++i].getDoubleValue();
            else if (a == "--wav") wavPath = args[++i];
            else if (a == "--snap") snapPath = args[++i];
            else if (a == "--rt") realtime = true;
            else if (a == "--editor") withEditor = true;
            else if (a == "--hold") holds.add (args[++i].getIntValue());
            else if (a == "--click") clicks.add (juce::Point<int> (args[i+1].upToFirstOccurrenceOf (",", false, false).getIntValue(), args[i+1].fromFirstOccurrenceOf (",", false, false).getIntValue())), ++i;
            else if (a == "--guiset") { auto kv = args[++i]; guiSets.push_back ({ kv.upToFirstOccurrenceOf ("=", false, false), kv.fromFirstOccurrenceOf ("=", false, false).getFloatValue() }); }
            else if (a == "--wait") waitMs = args[++i].getIntValue();
            else if (a == "--set" || a == "--settext")
            {
                auto kv = args[++i];
                auto* prm = findParam (*inst, kv.upToFirstOccurrenceOf ("=", false, false));
                if (! prm) { std::printf ("no param %s\n", kv.toRawUTF8()); continue; }
                auto v = kv.fromFirstOccurrenceOf ("=", false, false);
                float norm = a == "--set" ? v.getFloatValue() : prm->getValueForText (v);
                prm->setValueNotifyingHost (norm);
                {   // Cabbage drops bursts of parameter changes: let each one land
                    AudioBuffer<float> wb (2, block); auto end = Time::getMillisecondCounter() + 40;
                    while (Time::getMillisecondCounter() < end) { wb.clear(); MidiBuffer mm; inst->processBlock (wb, mm);
                        MessageManager::getInstance()->runDispatchLoopUntil (2); }
                }
                std::printf ("set %s -> %.4f (%s)\n", prm->getName (64).toRawUTF8(), norm, prm->getCurrentValueAsText().toRawUTF8());
            }
            else if (a == "--ccs")
            {
                for (auto n : StringArray::fromTokens (args[++i], ",", ""))
                {
                    auto t = StringArray::fromTokens (n, ":", "");
                    ccs.add ({ t[0].getIntValue(), t[1].getDoubleValue(), t[2].getIntValue(), t.size() > 3 ? t[3].getIntValue() : 1 });
                }
            }
            else if (a == "--notes")
            {
                for (auto n : StringArray::fromTokens (args[++i], ",", ""))
                {
                    auto t = StringArray::fromTokens (n, ":", "");
                    notes.add ({ t[0].getIntValue(), t[1].getDoubleValue(), t[2].getDoubleValue(), t.size() > 3 ? t[3].getIntValue() : 100 });
                }
            }
        }

        // let parameter changes propagate (Cabbage uses message thread / timers)
        AudioBuffer<float> pumpBuf (jmax (2, inst->getTotalNumOutputChannels()), block); double pumpPeak = 0; long pumpBlocks = 0; bool pendingHolds = false;
        auto pump = [&] (int ms) { auto end = Time::getMillisecondCounter() + (uint32) ms;
            while (Time::getMillisecondCounter() < end) {
                for (int k = 0; k < 2; ++k) { pumpBuf.clear(); MidiBuffer mm;
                    if (pendingHolds) { for (auto n : holds) mm.addEvent (MidiMessage::noteOn (1, n, (uint8) 100), 0); pendingHolds = false; }
                    inst->processBlock (pumpBuf, mm); pumpPeak = jmax (pumpPeak, (double) pumpBuf.getMagnitude (0, block)); ++pumpBlocks; }
                MessageManager::getInstance()->runDispatchLoopUntil (20); } };
        std::unique_ptr<AudioProcessorEditor> liveEd; std::unique_ptr<DocumentWindow> liveWin;
        if (withEditor)
        {
            liveEd.reset (inst->createEditorIfNeeded());
            liveWin = std::make_unique<DocumentWindow> ("live", Colours::black, 0);
            liveWin->setUsingNativeTitleBar (true);
            liveWin->setContentNonOwned (liveEd.get(), true);
            liveWin->setVisible (true);
        }
        pump (waitMs);

        if (wavPath.isNotEmpty())
        {
            const int total = (int) (secs * sr);
            const int nch = jmax (2, inst->getTotalNumOutputChannels()); AudioBuffer<float> out (2, total), b (nch, block); std::vector<double> chPeak ((size_t) nch, 0.0);
            MidiBuffer all;
            for (auto& [nn, st, du, ve] : notes)
            {
                all.addEvent (MidiMessage::noteOn (1, nn, (uint8) ve), (int) (st * sr));
                all.addEvent (MidiMessage::noteOff (1, nn), (int) ((st + du) * sr));
            }
            for (auto& [cn, ct, cv, cch] : ccs) all.addEvent (MidiMessage::controllerEvent (cch, cn, cv), (int) (ct * sr));
            double peak = 0, sum = 0; bool finite = true;
            for (int done = 0; done < total; done += block)
            {
                b.clear();
                MidiBuffer m;
                for (const auto meta : all)
                    if (meta.samplePosition >= done && meta.samplePosition < done + block)
                        m.addEvent (meta.getMessage(), meta.samplePosition - done);
                inst->processBlock (b, m);
                for (int c = 0; c < nch; ++c) chPeak[(size_t) c] = jmax (chPeak[(size_t) c], (double) b.getMagnitude (c, 0, block));
                const int n = jmin (block, total - done);
                for (int c = 0; c < 2; ++c)
                {
                    out.copyFrom (c, done, b, c, 0, n);
                    for (int s = 0; s < n; ++s) { auto v = b.getSample (c, s); if (! std::isfinite (v)) finite = false;
                        peak = jmax (peak, (double) std::abs (v)); sum += v * v; }
                }
                if (realtime) MessageManager::getInstance()->runDispatchLoopUntil ((int) (1000.0 * block / sr));
                else if ((done / block) % 16 == 0) MessageManager::getInstance()->runDispatchLoopUntil (1);
            }
            { std::printf ("chpeaks:"); for (auto v : chPeak) std::printf (" %.3f", v); std::printf ("\n"); }
            std::printf ("render: peak=%.4f rms=%.5f finite=%d\n", peak, std::sqrt (sum / (2.0 * total)), (int) finite);
            File f (wavPath); f.deleteFile();
            WavAudioFormat wav;
            std::unique_ptr<OutputStream> os (f.createOutputStream().release());
            auto w = wav.createWriterFor (os, AudioFormatWriterOptions{}.withSampleRate (sr).withNumChannels (2).withBitsPerSample (24));
            w->writeFromAudioSampleBuffer (out, 0, total);
        }

        if (snapPath.isNotEmpty())
        {
            std::unique_ptr<AudioProcessorEditor> ed (inst->createEditorIfNeeded());
            if (ed)
            {
                DocumentWindow win ("snap", Colours::black, 0);
                win.setUsingNativeTitleBar (true);
                win.setContentNonOwned (ed.get(), true);
                win.setTopLeftPosition (60, 60);
                win.setVisible (true);
                for (auto& kv : guiSets) { if (auto* prm = findParam (*inst, kv.first)) prm->setValueNotifyingHost (kv.second); }
                pendingHolds = ! holds.isEmpty();
                pump (1200);
                for (auto pt : clicks)
                {
                    auto* target = ed->getComponentAt (pt);
                    if (target == nullptr) continue;
                    auto local = target->getLocalPoint (ed.get(), pt.toFloat());
                    auto src = Desktop::getInstance().getMainMouseSource();
                    MouseEvent down (src, local, ModifierKeys (ModifierKeys::leftButtonModifier), 1.0f, 0, 0, 0, 0, target, target, Time::getCurrentTime(), local, Time::getCurrentTime(), 1, false);
                    target->mouseDown (down);
                    MouseEvent up (src, local, ModifierKeys(), 1.0f, 0, 0, 0, 0, target, target, Time::getCurrentTime(), local, Time::getCurrentTime(), 1, false);
                    target->mouseUp (up);
                    { juce::Component* t = target; while (t != nullptr && dynamic_cast<Button*> (t) == nullptr) t = t->getParentComponent(); if (auto* b = dynamic_cast<Button*> (t)) { b->triggerClick(); std::printf ("button %s\n", b->getButtonText().toRawUTF8()); } else std::printf ("no button (%s)\n", typeid (*target).name()); }
                    std::printf ("clicked %s at %d,%d\n", target->getName().toRawUTF8(), pt.x, pt.y);
                    pump (400);
                }
                pump (jmax (1500, waitMs));
                {
                    auto* view = (NSView*) win.getWindowHandle();
                    long wn = (long) [[view window] windowNumber];
                    String cmd = "screencapture -x -o -l" + String ((int64) wn) + " \"" + snapPath + "\"";
                    std::system (cmd.toRawUTF8());
                    if (auto* bn = std::getenv ("KH_BURST")) for (int k = 0; k < atoi (bn); ++k) { pump (40); String c2 = "screencapture -x -o -l" + String ((int64) wn) + " \"" + snapPath + "." + String (k) + ".png\""; std::system (c2.toRawUTF8()); }
                }
                auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 1.0f);
                File f (snapPath + ".juce.png"); f.deleteFile();
                PNGImageFormat png; FileOutputStream fos (f); png.writeImageToStream (img, fos);
                std::printf ("snap %dx%d\n", img.getWidth(), img.getHeight()); std::printf ("pump blocks=%ld peak=%.4f\n", pumpBlocks, pumpPeak);
                win.clearContentComponent();
                inst->editorBeingDeleted (ed.get());
            }
        }
        if (liveWin) { liveWin->clearContentComponent(); inst->editorBeingDeleted (liveEd.get()); liveEd.reset(); liveWin.reset(); }
        inst->releaseResources();
        return 0;
    }
};

START_JUCE_APPLICATION (App)
