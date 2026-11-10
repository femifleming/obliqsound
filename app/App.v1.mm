// ObliqSound desktop app: a dedicated standalone host for the bundled ObliqSound.vst3.
// - audio + MIDI device setup (Options menu), all MIDI inputs enabled, hot-plug aware
// - computer keyboard plays notes (A W S E D F T G Y H U J K ; Z/X = octave, C/V = velocity)
// - plugin state + device settings persist in ~/Library/Application Support/ObliqSound
#include <juce_audio_utils/juce_audio_utils.h>
#import <AppKit/AppKit.h>
using namespace juce;

static File supportDir() { auto d = File::getSpecialLocation (File::userApplicationDataDirectory).getChildFile ("Application Support/ObliqSound"); d.createDirectory(); return d; }

static File findPlugin()
{
    auto bundled = File::getSpecialLocation (File::currentApplicationFile).getChildFile ("Contents/PlugIns/ObliqSound.vst3");
    if (bundled.exists()) return bundled;
    auto user = File::getSpecialLocation (File::userHomeDirectory).getChildFile ("Library/Audio/Plug-Ins/VST3/ObliqSound.vst3");
    if (user.exists()) return user;
    return File ("/Library/Audio/Plug-Ins/VST3/ObliqSound.vst3");
}

class MainWindow : public DocumentWindow, public MenuBarModel, private Timer
{
public:
    MainWindow (AudioPluginInstance& p, AudioDeviceManager& dm, MidiMessageCollector& mc)
        : DocumentWindow ("ObliqSound", Colour (0xff1c2a22), DocumentWindow::closeButton | DocumentWindow::minimiseButton),
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
        return m;
    }
    void menuItemSelected (int id, int) override
    {
        if (id == 1) showSettings();
        if (id == 2) { keysOn = ! keysOn; if (! keysOn) allNotesOff(); menuItemsChanged(); }
        if (id == 3) allNotesOff();
    }
    void showSettings()
    {
        auto* sel = new AudioDeviceSelectorComponent (devices, 0, 2, 0, 2, true, false, true, false);
        sel->setSize (520, 460);
        DialogWindow::LaunchOptions o;
        o.content.setOwned (sel);
        o.dialogTitle = "ObliqSound - Audio / MIDI Settings";
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
    const String getApplicationName() override { return "ObliqSound"; }
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
            { NSAlert* al = [[NSAlert alloc] init]; al.messageText = @"ObliqSound"; al.informativeText = [NSString stringWithUTF8String: String ("Could not load the ObliqSound engine (" + file.getFullPathName() + ").\n" + err).toRawUTF8()]; [al runModal]; }
            quit(); return;
        }
        plugin->disableNonMainBuses();
        plugin->setPlayConfigDetails (0, 2, 48000, 512);

        // devices
        auto devXml = parseXML (supportDir().getChildFile ("devices.xml"));
        deviceManager.initialise (0, 2, devXml.get(), true);
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

        player.setProcessor (plugin.get());
        deviceManager.addAudioCallback (&player);
        deviceManager.addMidiInputDeviceCallback ({}, &player);

        window = std::make_unique<MainWindow> (*plugin, deviceManager, player.getMidiMessageCollector());
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
        deviceManager.removeMidiInputDeviceCallback ({}, &player);
        deviceManager.removeAudioCallback (&player);
        player.setProcessor (nullptr);
        midiWatch = nullptr;
        plugin = nullptr;
        deviceManager.closeAudioDevice();
    }
    void systemRequestedQuit() override { quit(); }

private:
    AudioDeviceManager deviceManager;
    AudioProcessorPlayer player;
    std::unique_ptr<AudioPluginInstance> plugin;
    std::unique_ptr<MainWindow> window;
    std::unique_ptr<MidiDeviceListConnection> midiWatch;
};

START_JUCE_APPLICATION (ObliqApp)
