// ObliqSound / ObliqSonic desktop app: a dedicated standalone host for the bundled plug-in (OBLIQ_NAME).
// ObliqSonic (OBLIQ_SONIC=1) outputs either a stereo decode of its Ambisonics or the raw 16 channels.
// - audio + MIDI device setup (Options menu), all MIDI inputs enabled, hot-plug aware
// - computer keyboard plays notes (A W S E D F T G Y H U J K ; Z/X = octave, C/V = velocity)
// - plugin state + device settings persist in ~/Library/Application Support/<name>
#include <juce_audio_utils/juce_audio_utils.h>
#ifndef OBLIQ_NAME
 #define OBLIQ_NAME "ObliqSound"
#endif
#ifndef OBLIQ_SONIC
 #define OBLIQ_SONIC 0
#endif
#import <AppKit/AppKit.h>
using namespace juce;

static File supportDir() { auto d = File::getSpecialLocation (File::userApplicationDataDirectory).getChildFile (String ("Application Support/") + OBLIQ_NAME); d.createDirectory(); return d; }

static File findPlugin()
{
    auto bundled = File::getSpecialLocation (File::currentApplicationFile).getChildFile (String ("Contents/PlugIns/") + OBLIQ_NAME + ".vst3");
    if (bundled.exists()) return bundled;
    auto user = File::getSpecialLocation (File::userHomeDirectory).getChildFile (String ("Library/Audio/Plug-Ins/VST3/") + OBLIQ_NAME + ".vst3");
    if (user.exists()) return user;
    return File (String ("/Library/Audio/Plug-Ins/VST3/") + OBLIQ_NAME + ".vst3");
}

// Runs the plug-in from the audio device. For a multichannel (Ambisonics) plug-in it either passes
// all its channels to the device or decodes them to stereo as a pair of virtual cardioids at +-60 deg.
class Engine : public AudioIODeviceCallback
{
public:
    Engine() { collector.reset (48000.0); }
    AudioPluginInstance* plugin = nullptr;
    MidiMessageCollector collector;
    std::atomic<int> outMode { 0 };          // 0 = stereo decode, 1 = all channels
    void audioDeviceAboutToStart (AudioIODevice* d) override
    {
        const double sr = d->getCurrentSampleRate(); const int bs = d->getCurrentBufferSizeSamples();
        nPlug = jmax (2, plugin->getTotalNumInputChannels(), plugin->getTotalNumOutputChannels());
        buf.setSize (nPlug, jmax (bs, 4096));
        plugin->setRateAndBufferSizeDetails (sr, bs);
        plugin->prepareToPlay (sr, bs);
        collector.reset (sr);
    }
    void audioDeviceStopped() override { plugin->releaseResources(); }
    void audioDeviceIOCallbackWithContext (const float* const*, int, float* const* out, int nOut, int n, const AudioIODeviceCallbackContext&) override
    {
        if (n > buf.getNumSamples()) buf.setSize (nPlug, n, false, false, true);
        AudioBuffer<float> b (buf.getArrayOfWritePointers(), nPlug, n);
        b.clear(); midi.clear();
        collector.removeNextBlockOfMessages (midi, n);
        {
            const ScopedLock sl (plugin->getCallbackLock());
            if (! plugin->isSuspended()) plugin->processBlock (b, midi);
        }
        for (int c = 0; c < nOut; ++c) if (out[c] != nullptr) FloatVectorOperations::clear (out[c], n);
        const int pOut = plugin->getTotalNumOutputChannels();
        if (pOut <= 2 || outMode.load() == 1)
        {
            for (int c = 0; c < jmin (nOut, pOut); ++c) if (out[c] != nullptr) FloatVectorOperations::copy (out[c], b.getReadPointer (c), n);
        }
        else
        {   // ACN/SN3D: W = 0, Y = 1, X = 3. Cardioid towards azimuth a: 0.5 * (W + cos(a) X + sin(a) Y), y = left
            const float* W = b.getReadPointer (0); const float* Y = b.getReadPointer (1); const float* X = b.getReadPointer (3);
            for (int i = 0; i < n; ++i)
            {
                const float l = 0.5f * (W[i] + 0.5f * X[i] + 0.866f * Y[i]);
                const float r = 0.5f * (W[i] + 0.5f * X[i] - 0.866f * Y[i]);
                if (nOut > 0 && out[0] != nullptr) out[0][i] = nOut > 1 ? l : W[i];
                if (nOut > 1 && out[1] != nullptr) out[1][i] = r;
            }
        }
    }
private:
    AudioBuffer<float> buf; MidiBuffer midi; int nPlug = 2;
};

class MainWindow : public DocumentWindow, public MenuBarModel, private Timer
{
public:
    MainWindow (AudioPluginInstance& p, AudioDeviceManager& dm, MidiMessageCollector& mc, Engine& en)
        : engine (en), DocumentWindow (OBLIQ_NAME, Colour (0xff1c2a22), DocumentWindow::closeButton | DocumentWindow::minimiseButton),
          plugin (p), devices (dm), collector (mc)
    {
        setUsingNativeTitleBar (true);
        editor.reset (plugin.createEditorIfNeeded());
        setContentNonOwned (editor.get(), true);
        setResizable (false, false);
        auto pos = supportDir().getChildFile ("window.txt").loadFileAsString();
        if (pos.isNotEmpty()) restoreWindowStateFromString (pos); else centreWithSize (getWidth(), getHeight());
        setVisible (true);
        MenuBarModel::setMacMainMenu (this);
        installKeyMonitor();
        startTimer (30000);   // autosave
    }
    ~MainWindow() override
    {
        stopTimer();
        if (keyMonitor) { [NSEvent removeMonitor: keyMonitor]; keyMonitor = nil; }
        allNotesOff();
        MenuBarModel::setMacMainMenu (nullptr);
        supportDir().getChildFile ("window.txt").replaceWithText (getWindowStateAsString());
        clearContentComponent();
        if (editor) plugin.editorBeingDeleted (editor.get());
        editor = nullptr;
    }
    void closeButtonPressed() override { JUCEApplication::getInstance()->systemRequestedQuit(); }

    StringArray getMenuBarNames() override { return { "Options" }; }
    PopupMenu getMenuForIndex (int, const String&) override
    {
        PopupMenu m;
        m.addItem (1, "Audio / MIDI Settings...");
        m.addItem (2, "Computer Keyboard Plays Notes", true, keysOn);
        m.addSeparator();
        m.addItem (3, "All Notes Off");
       #if OBLIQ_SONIC
        m.addSeparator();
        m.addItem (4, "Output: Stereo (decoded from the Ambisonics)", true, engine.outMode.load() == 0);
        m.addItem (5, "Output: 16-channel Ambisonics (ACN / SN3D, for a decoder)", true, engine.outMode.load() == 1);
       #endif
        return m;
    }
    void menuItemSelected (int id, int) override
    {
        if (id == 1) showSettings();
        if (id == 2) { keysOn = ! keysOn; if (! keysOn) allNotesOff(); menuItemsChanged(); }
        if (id == 3) allNotesOff();
        if (id == 4 || id == 5)
        {
            engine.outMode = id - 4;
            supportDir().getChildFile ("output.txt").replaceWithText (String (id - 4));
            menuItemsChanged();
            if (id == 5 && devices.getCurrentAudioDevice() != nullptr
                && devices.getCurrentAudioDevice()->getActiveOutputChannels().countNumberOfSetBits() < 16)
                AlertWindow::showMessageBoxAsync (MessageBoxIconType::InfoIcon, OBLIQ_NAME,
                    "The current output device has fewer than 16 outputs, so only the first channels are heard.\n\n"
                    "Choose a device with 16 or more outputs in Audio / MIDI Settings (for example a 16-channel "
                    "virtual device feeding REAPER and an IEM decoder), or use Output: Stereo.");
        }
    }
    void showSettings()
    {
        auto* sel = new AudioDeviceSelectorComponent (devices, 0, 2, 0, 2, true, false, true, false);
        sel->setSize (520, 460);
        DialogWindow::LaunchOptions o;
        o.content.setOwned (sel);
        o.dialogTitle = String (OBLIQ_NAME) + " - Audio / MIDI Settings";
        o.dialogBackgroundColour = Colour (0xff23302a);
        o.useNativeTitleBar = true; o.resizable = false;
        o.launchAsync();
    }
    void allNotesOff()
    {
        for (int n : held) send (MidiMessage::noteOff (1, n));
        held.clear(); pressed.clear();
        for (int c = 1; c <= 16; ++c) send (MidiMessage::allNotesOff (c));
    }
    std::function<void()> autosave;

private:
    void timerCallback() override { if (autosave) autosave(); }
    void send (MidiMessage m) { m.setTimeStamp (Time::getMillisecondCounterHiRes() * 0.001); collector.addMessageToQueue (m); }

    int keyToNote (unsigned short code) const
    {   // mac virtual key codes, layout-independent (row A S D F ... like a DAW keyboard)
        static const std::map<unsigned short, int> map {
            {0,0},{13,1},{1,2},{14,3},{2,4},{3,5},{17,6},{5,7},{16,8},{4,9},{32,10},{38,11},{40,12},{31,13},{37,14},{35,15},{41,16},{39,17} };
        auto it = map.find (code); return it == map.end() ? -1 : it->second;
    }
    bool textFieldFocused() const
    {
        NSResponder* r = [[NSApp keyWindow] firstResponder];
        return r != nil && ([r isKindOfClass: [NSText class]] || [r isKindOfClass: [NSTextField class]]
                            || dynamic_cast<TextEditor*> (Component::getCurrentlyFocusedComponent()) != nullptr);
    }
    void installKeyMonitor()
    {
        keyMonitor = [NSEvent addLocalMonitorForEventsMatchingMask: (NSEventMaskKeyDown | NSEventMaskKeyUp)
                                                           handler: ^NSEvent* (NSEvent* e) {
            if (! keysOn || ([e modifierFlags] & (NSEventModifierFlagCommand | NSEventModifierFlagControl)) || textFieldFocused()
                || [e window] != (NSWindow*) [(NSView*) getWindowHandle() window])
                return e;
            const bool down = [e type] == NSEventTypeKeyDown;
            const unsigned short code = [e keyCode];
            if (down && [e isARepeat]) return keyToNote (code) >= 0 || code == 6 || code == 7 || code == 8 || code == 9 ? nil : e;
            if (down && (code == 6 || code == 7)) { octave = jlimit (-3, 4, octave + (code == 6 ? -1 : 1)); return nil; }       // Z / X
            if (down && (code == 8 || code == 9)) { velocity = jlimit (10, 127, velocity + (code == 8 ? -20 : 20)); return nil; } // C / V
            int k = keyToNote (code);
            if (k < 0) return e;
            if (down)
            {
                if (pressed.count (code)) return nil;
                int n = jlimit (0, 127, 60 + 12 * octave + k);
                pressed[code] = n; held.insert (n);
                send (MidiMessage::noteOn (1, n, (uint8) velocity));
            }
            else if (auto it = pressed.find (code); it != pressed.end())
            {
                send (MidiMessage::noteOff (1, it->second)); held.erase (it->second); pressed.erase (it);
            }
            return nil;
        }];
    }

    Engine& engine;
    AudioPluginInstance& plugin;
    AudioDeviceManager& devices;
    MidiMessageCollector& collector;
    std::unique_ptr<AudioProcessorEditor> editor;
    id keyMonitor = nil;
    bool keysOn = true;
    int octave = 0, velocity = 100;
    std::map<unsigned short, int> pressed;
    std::set<int> held;
};

class ObliqApp : public JUCEApplication
{
public:
    const String getApplicationName() override { return OBLIQ_NAME; }
    const String getApplicationVersion() override { return "1.0"; }
    bool moreThanOneInstanceAllowed() override { return false; }

    void initialise (const String&) override
    {
        auto file = findPlugin();
        OwnedArray<PluginDescription> descs;
        VST3PluginFormat vst3;
        vst3.findAllTypesForFile (descs, file.getFullPathName());
        String err;
        if (! descs.isEmpty())
        {
            AudioPluginFormatManager fm; addDefaultFormatsToManager (fm);
            plugin = fm.createPluginInstance (*descs[0], 48000, 512, err);
        }
        if (! plugin)
        {
            { NSAlert* al = [[NSAlert alloc] init]; al.messageText = @OBLIQ_NAME; al.informativeText = [NSString stringWithUTF8String: String ("Could not load the " OBLIQ_NAME " engine (" + file.getFullPathName() + ").\n" + err).toRawUTF8()]; [al runModal]; }
            quit(); return;
        }
       #if ! OBLIQ_SONIC
        plugin->disableNonMainBuses();
        plugin->setPlayConfigDetails (0, 2, 48000, 512);
       #endif
       // ObliqSonic: leave the bus layout alone (all 16 outputs are on by default; changing it upsets Cabbage)

        // devices
        auto devXml = parseXML (supportDir().getChildFile ("devices.xml"));
        // a device that hung us last time (the marker survived) is skipped: start on the default output
        auto marker = supportDir().getChildFile ("opening-audio-device");
        String skipped;
        if (marker.existsAsFile() && devXml != nullptr)
        {
            skipped = devXml->getStringAttribute ("audioOutputDeviceName");
            devXml = nullptr;
        }
        if (devXml != nullptr && devXml->getIntAttribute ("audioDeviceBufferSize") <= 0)
            devXml->setAttribute ("audioDeviceBufferSize", 256);
        marker.replaceWithText ("1");
        deviceManager.initialise (0, OBLIQ_SONIC ? 16 : 2, devXml.get(), true);
        marker.deleteFile();
        if (skipped.isNotEmpty())
            MessageManager::callAsync ([skipped] {
                AlertWindow::showMessageBoxAsync (MessageBoxIconType::WarningIcon, OBLIQ_NAME,
                    "The audio device \"" + skipped + "\" didn't open last time, so " OBLIQ_NAME " started on the default output.\n"
                    "Choose a device again in Options > Audio / MIDI Settings.");
            });
        if (! devXml)
        {   // first launch: prefer the system default output at 48k / 256
            auto setup = deviceManager.getAudioDeviceSetup();
            setup.sampleRate = 48000; setup.bufferSize = 256;
            deviceManager.setAudioDeviceSetup (setup, true);
        }
        enableAllMidiInputs();
        midiWatch = std::make_unique<MidiDeviceListConnection> (MidiDeviceListConnection::make ([this] { enableAllMidiInputs(); }));

        // state
        MemoryBlock mb;
        if (supportDir().getChildFile ("state.bin").loadFileAsData (mb) && mb.getSize() > 0)
            plugin->setStateInformation (mb.getData(), (int) mb.getSize());

        engine.plugin = plugin.get();
        engine.outMode = supportDir().getChildFile ("output.txt").loadFileAsString().getIntValue();
        deviceManager.addAudioCallback (&engine);
        deviceManager.addMidiInputDeviceCallback ({}, &engine.collector);

        window = std::make_unique<MainWindow> (*plugin, deviceManager, engine.collector, engine);
        window->autosave = [this] { saveAll(); };
    }

    void enableAllMidiInputs()
    {
        for (auto& d : MidiInput::getAvailableDevices())
            if (! deviceManager.isMidiInputDeviceEnabled (d.identifier))
                deviceManager.setMidiInputDeviceEnabled (d.identifier, true);
    }

    void saveAll()
    {
        if (! plugin) return;
        MemoryBlock mb; plugin->getStateInformation (mb);
        if (mb.getSize() > 0) supportDir().getChildFile ("state.bin").replaceWithData (mb.getData(), mb.getSize());
        if (auto xml = deviceManager.createStateXml()) xml->writeTo (supportDir().getChildFile ("devices.xml"));
    }

    void shutdown() override
    {
        saveAll();
        if (window) window->allNotesOff();
        window = nullptr;
        deviceManager.removeMidiInputDeviceCallback ({}, &engine.collector);
        deviceManager.removeAudioCallback (&engine);
        midiWatch = nullptr;
        plugin = nullptr;
        deviceManager.closeAudioDevice();
    }
    void systemRequestedQuit() override { quit(); }

private:
    AudioDeviceManager deviceManager;
    Engine engine;
    std::unique_ptr<AudioPluginInstance> plugin;
    std::unique_ptr<MainWindow> window;
    std::unique_ptr<MidiDeviceListConnection> midiWatch;
};

START_JUCE_APPLICATION (ObliqApp)
