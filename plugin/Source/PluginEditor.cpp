#include "PluginEditor.h"
#include "Help.h"
#if JucePlugin_Build_Standalone
 #include <juce_audio_utils/juce_audio_utils.h>
 #include <juce_audio_plugin_client/Standalone/juce_StandaloneFilterWindow.h>
#endif

using juce::String; using juce::Colour; using juce::Rectangle;

namespace
{
    enum Dyn { dNone, dWave, dSampLabel, dLcd, dL1, dL2, dFol, dOut, dVLed, dSubLed, dBoid, dLz, dSpd, dLesA, dLesB, dSpMode, dLesAn, dLesBn, dSpec };
    const char* kKeys = "awsedftgyhujkolp;'";
    String modeName (float m)
    {
        const float k = std::round (m * 2.0f) / 2.0f;
        if (k < 0.25f) return "LP"; if (k < 0.75f) return "LP>BP"; if (k < 1.25f) return "BP"; if (k < 1.75f) return "BP>HP";
        if (k < 2.25f) return "HP"; if (k < 2.75f) return "HP>NOTCH"; if (k < 3.25f) return "NOTCH"; if (k < 3.75f) return "NOTCH>COMB";
        return "COMB";
    }
}

// =================================================================================================== build
ObliqPanel::ObliqPanel (ObliqProcessor& p) : proc (p), params (p.params)
{
    artDir = ObliqProcessor::resourceDir().getChildFile ("art");
    juce::MemoryBlock mb;
    if (artDir.getChildFile ("Tahoma Bold.ttf").loadFileAsData (mb)) face = juce::Typeface::createSystemTypefaceFor (mb.getData(), mb.getSize());
    juce::ImageCache::setCacheTimeout (3000);
    build();
    setOpaque (true);
    setWantsKeyboardFocus (true);
    lfoH[0].assign (256, 0.0f); lfoH[1].assign (256, 0.0f);
    bg = art (bgName (0, 0, 0));
    if (auto h = juce::SystemStats::getEnvironmentVariable ("OBLIQ_HELP", {}); h.isNotEmpty()) { helpOpen = true; helpTopic = h.getIntValue(); }   // for screenshots
    startTimerHz (30);
}

ObliqPanel::~ObliqPanel() { stopTimer(); for (auto& k : heldKeys) proc.keyboard.noteOff (1, k.second, 0.0f); }

juce::Image ObliqPanel::art (const String& file)
{
    if (file.isEmpty()) return {};
    return juce::ImageCache::getFromFile (artDir.getChildFile (file));
}

String ObliqPanel::bgName (int pg, int morph, int idleFrame) const
{
    if (morph > 0) return prefix + "bg_" + String (pg + 1) + "_" + String (morph) + ".png";
    if (idleFrame > 0) return prefix + "bg_" + String (pg + 1) + "_i" + String (idleFrame) + ".png";
    return prefix + "bg_" + String (pg + 1) + "_0.png";
}

void ObliqPanel::build()
{
    const auto& lay = proc.layout;
    if (auto* sz = lay["size"].getArray()) { baseW = (int) (*sz)[0]; baseH = (int) (*sz)[1]; }
    auto* ws = lay["widgets"].getArray();
    if (ws == nullptr) return;
    for (auto& w : *ws)
    {
        const String type = w["type"].toString(), ch = w["channel"].toString();
        auto* b = w["bounds"].getArray(); if (b == nullptr) continue;
        Rectangle<int> r ((int) (*b)[0], (int) (*b)[1], (int) (*b)[2], (int) (*b)[3]);
        if (ch == "image6") { prefix = w["file"].toString().upToFirstOccurrenceOf ("bg_", false, false); continue; }
        if ((bool) w["container"])
        {
            pageNames.add (ch); pageBounds.push_back (r); pageImage.push_back (art (w["file"].toString())); pageStart.push_back ((int) items.size());
            continue;
        }
        Item it; it.channel = ch; it.file = w["file"].toString(); it.popup = w["popup"].toString(); it.group = w["group"].toString();
        it.page = pageNames.indexOf (w["page"].toString());
        if (it.page >= 0) r = r.translated (pageBounds[(size_t) it.page].getX(), pageBounds[(size_t) it.page].getY());
        it.r = r;
        it.param = params.find (ch);
        if (w.hasProperty ("alpha")) it.alpha = (float) (double) w["alpha"];
        if (w.hasProperty ("visible")) it.visible = (int) w["visible"] != 0;
        if (auto* ink = w["ink"].getArray()) it.ink = Colour ((juce::uint8) (int) (*ink)[0], (juce::uint8) (int) (*ink)[1], (juce::uint8) (int) (*ink)[2], (juce::uint8) (ink->size() > 3 ? (int) (*ink)[3] : 255));
        if (auto* t = w["text"].getArray()) for (auto& s : *t) it.text.add (s.toString());
        if (auto* sg = w["signals"].getArray()) for (auto& s : *sg) it.signals.add (s.toString());
        if (type == "image") { it.type = Image; it.img = art (it.file); }
        else if (type == "rslider") { it.type = Knob; it.img = art (w["strip"].toString()); it.frames = (int) w["frames"]; }
        else if (type == "vslider") { it.type = VSlider; it.img = art (w["cap"].toString()); }
        else if (type == "nslider") it.type = NSlider;
        else if (type == "checkbox") { it.type = Check; it.img = art (w["on"].toString()); it.img2 = art (w["off"].toString()); }
        else if (type == "combobox")
        {
            if ((bool) w["presets"]) it.type = PresetBox;
            else if (w["mode"].toString() == "resize") { it.type = SizeBox; it.text = { "50%", "75%", "100%", "125%", "150%", "200%" }; }
            else it.type = Combo;
        }
        else if (type == "button") it.type = Button;
        else if (type == "filebutton") it.type = w["mode"].toString().contains ("remove") ? PresetRemove : PresetSave;
        else if (type == "label") it.type = Label;
        else if (type == "signaldisplay") it.type = Scope;
        else continue;
        // engine-driven elements
        auto num = [&] (const char* pre) { return ch.startsWith (pre) && ch.substring ((int) std::strlen (pre)).containsOnly ("0123456789") && ch.length() > (int) std::strlen (pre); };
        auto idx = [&] (const char* pre) { return ch.substring ((int) std::strlen (pre)).getIntValue(); };
        if (num ("Swave")) { it.dyn = dWave; it.dynIndex = idx ("Swave"); }
        else if (num ("sl")) { it.dyn = dSampLabel; it.dynIndex = idx ("sl"); }
        else if (ch == "lcdText") it.dyn = dLcd;
        else if (ch == "l1Led") it.dyn = dL1; else if (ch == "l2Led") it.dyn = dL2;
        else if (ch == "fLed") it.dyn = dFol; else if (ch == "oLed") it.dyn = dOut;
        else if (ch == "vLed") it.dyn = dVLed; else if (ch == "subLed") it.dyn = dSubLed;
        else if (num ("bd")) { it.dyn = dBoid; it.dynIndex = idx ("bd") - 1; }
        else if (num ("lz")) { it.dyn = dLz; it.dynIndex = idx ("lz"); }
        else if (num ("spd")) { it.dyn = dSpd; it.dynIndex = idx ("spd"); }
        else if (num ("sp") && it.type == Image) it.dyn = dSpec;
        else if (ch == "lesA") it.dyn = dLesA; else if (ch == "lesB") it.dyn = dLesB;
        else if (ch == "lesAn") it.dyn = dLesAn; else if (ch == "lesBn") it.dyn = dLesBn;
        else if (ch == "spModeTxt") it.dyn = dSpMode;
        if (it.group == "200") tabParams.push_back (it.param);
        items.push_back (it);
    }
    // the Help button takes the right end of the preset list, so the header stays mirrored
    for (size_t i = 0; i < items.size(); ++i)
        if (items[i].type == PresetBox)
        {
            Item h; h.type = Help; h.channel = "help"; h.text = { "Help" };
            h.r = items[i].r.removeFromRight (56).withTrimmedLeft (4);
            items.push_back (h);
            break;
        }
}

// =================================================================================================== timer: pages, background, meters
void ObliqPanel::changePage (int to) { pending = to; }

void ObliqPanel::timerCallback()
{
    ++tickCount;
    // which tab is on
    int want = pending >= 0 ? pending : page;
    for (size_t i = 0; i < tabParams.size(); ++i) if ((int) i != want && params.get (tabParams[i]) > 0.5f) { want = (int) i; break; }
    for (size_t i = 0; i < tabParams.size(); ++i) { const float on = (int) i == want ? 1.0f : 0.0f; if (params.get (tabParams[i]) != on) params.set (tabParams[i], on); }
    if (want != page && anim == 0) pending = want;

    String name;
    if (anim > 0)
    {   // the land flows from the old page's shape through the shared middle shape into the new one
        name = anim <= kNfr ? bgName (fromPage, anim, 0) : bgName (page, 2 * kNfr - anim, 0);
        if (++anim > 2 * kNfr) { anim = 0; idle = 0; }
    }
    else if (pending >= 0 && pending != page)
    {   // run the land quickly back to its resting shape, then morph
        if (idle != 0) { idle = idle < kNidle / 2 ? juce::jmax (idle - 6, 0) : (idle + 6 >= kNidle ? 0 : idle + 6); name = bgName (page, 0, idle); }
        else { fromPage = page; page = pending; pending = -1; anim = 1; name = bgName (fromPage, 1, 0); }
    }
    else if (tickCount % 3 == 0 && pageNames[page] != "matpanel")
    {   // idle: wander back and forth through the loop of shapes so the motion never repeats
        if (random.nextFloat() < 0.012f) idleDir = -idleDir;
        idle = (idle + idleDir * 2 + kNidle) % kNidle;
        name = bgName (page, 0, idle);
    }
    if (name.isNotEmpty()) { auto im = art (name); if (im.isValid()) bg = im; }

    // histories for the scopes and the Lorenz trail
    auto& v = proc.engine->view;
    for (int l = 0; l < 2; ++l) { lfoH[l].erase (lfoH[l].begin()); lfoH[l].push_back (l == 0 ? v.lfo1.load() : v.lfo2.load()); }
    if (tickCount % 3 == 0) { for (int i = 23; i > 0; --i) { lzx[(size_t) i] = lzx[(size_t) i - 1]; lzy[(size_t) i] = lzy[(size_t) i - 1]; } lzx[0] = v.lorX; lzy[0] = -v.lorZ.load(); }
    if (proc.presetVersion.load() != lastPresetVersion) { lastPresetVersion = proc.presetVersion.load(); layerChange = -1; }
   #if JucePlugin_Build_Standalone
    // the desktop app listens to every MIDI input, including ones plugged in later
    if (tickCount % 60 == 1)
        if (auto* holder = juce::StandalonePluginHolder::getInstance())
            for (auto& d : juce::MidiInput::getAvailableDevices())
                if (! holder->deviceManager.isMidiInputDeviceEnabled (d.identifier)) holder->deviceManager.setMidiInputDeviceEnabled (d.identifier, true);
   #endif
    repaint();
}

// =================================================================================================== drawing
void ObliqPanel::drawItem (juce::Graphics& g, const Item& it)
{
    const auto r = it.r.toFloat();
    auto font = [&] (float h) { return face != nullptr ? juce::Font (juce::FontOptions (face).withHeight (h)) : juce::Font (juce::FontOptions (h, juce::Font::bold)); };
    switch (it.type)
    {
        case Image:
        {
            if (! it.img.isValid()) break;
            float a = it.alpha; bool vis = it.visible; juce::Image im = it.img;
            if (it.dyn == dWave) { const int wv = (int) std::lrint (params.get ("waveform")); vis = (it.dynIndex == 1 && wv == 4) || (it.dynIndex == 2 && wv == 3) || (it.dynIndex == 3 && wv == 2) || (it.dynIndex == 4 && wv == 1); }
            else if (it.dyn == dSampLabel) a = proc.engine->view.sampler.load() == it.dynIndex ? 1.0f : 0.5f;
            else if (it.dyn == dLcd) { im = art (prefix + "lcd_" + String (juce::jlimit (1, 26, proc.engine->view.sampler.load())) + ".png"); }
            if (! vis || ! im.isValid()) break;
            g.setOpacity (a); g.drawImage (im, r); g.setOpacity (1.0f);
            break;
        }
        case Knob:
        {
            if (! it.img.isValid() || it.param < 0) break;
            const int fh = it.img.getHeight() / juce::jmax (1, it.frames);
            const auto& d = params.def (it.param);
            // the strips are linear in value (the skew only shapes the drag), as the original panel drew them
            float lin = d.hi != d.lo ? (params.get (it.param) - d.lo) / (d.hi - d.lo) : 0.0f;
            lin = d.skew == 1.0f ? lin : params.toNorm (it.param, params.get (it.param));
            const int f = juce::jlimit (0, it.frames - 1, (int) std::lrint (lin * (float) (it.frames - 1)));
            g.drawImage (it.img, it.r.getX(), it.r.getY(), it.r.getWidth(), it.r.getHeight(), 0, f * fh, it.img.getWidth(), fh);
            break;
        }
        case VSlider:
        {
            if (it.param < 0) break;
            const float n = params.toNorm (it.param, params.get (it.param));
            const float ch = 12.0f, y = r.getY() + 2.0f + (1.0f - n) * (r.getHeight() - ch - 4.0f);
            if (it.img.isValid()) g.drawImage (it.img, Rectangle<float> (r.getX(), y, r.getWidth(), ch));
            break;
        }
        case NSlider:
        {
            g.setColour (juce::Colours::white); g.fillRect (r); g.setColour (juce::Colours::black); g.drawRect (r, 1.0f);
            g.setFont (font (11.0f)); g.drawText (String ((int) std::lrint (params.get (it.param))), it.r, juce::Justification::centred);
            break;
        }
        case Check:
        {
            const bool on = it.param >= 0 && params.get (it.param) > 0.5f;
            const auto& im = on ? it.img : it.img2;
            if (im.isValid()) g.drawImage (im, r);
            break;
        }
        case Combo: case PresetBox: case SizeBox:
        {
            g.setColour (juce::Colours::white); g.fillRect (r); g.setColour (juce::Colours::black); g.drawRect (r, 1.0f);
            String t;
            if (it.type == PresetBox) t = proc.currentPreset;
            else if (it.type == SizeBox) t = String ((int) std::lrint (scale * 100.0f)) + "%";
            else if (it.param >= 0) t = it.text[juce::jlimit (0, it.text.size() - 1, (int) std::lrint (params.get (it.param)) - 1)];
            g.setFont (font (juce::jmin (12.0f, r.getHeight() - 5.0f)));
            g.drawFittedText (t, it.r.reduced (3, 0).withTrimmedRight (10), juce::Justification::centredLeft, 1, 0.6f);
            juce::Path p; const float ax = r.getRight() - 11.0f, ay = r.getCentreY() - 2.0f;
            p.addTriangle (ax, ay, ax + 7.0f, ay, ax + 3.5f, ay + 4.5f); g.fillPath (p);
            break;
        }
        case Button: case PresetSave: case PresetRemove: case Help:
        {
            g.setColour (Colour (200, 204, 200)); g.fillRect (r); g.setColour (juce::Colours::white); g.drawLine (r.getX(), r.getY(), r.getRight(), r.getY()); g.drawLine (r.getX(), r.getY(), r.getX(), r.getBottom());
            g.setColour (Colour (70, 74, 70)); g.drawLine (r.getX(), r.getBottom(), r.getRight(), r.getBottom()); g.drawLine (r.getRight(), r.getY(), r.getRight(), r.getBottom());
            g.setColour (juce::Colours::black); g.setFont (font (12.0f)); g.drawText (it.text.isEmpty() ? String() : it.text[0], it.r, juce::Justification::centred);
            break;
        }
        case Label:
        {
            String t = it.text.isEmpty() ? String() : it.text[0];
            auto& v = proc.engine->view;
            if (it.dyn == dLesA) t = String ((int) v.cutA.load()) + " Hz   res " + String ((int) std::lrint (v.resA.load() * 100.0f)) + "   " + modeName (v.modeA);
            else if (it.dyn == dLesB) t = String ((int) v.cutB.load()) + " Hz   res " + String ((int) std::lrint (v.resB.load() * 100.0f)) + "   " + modeName (v.modeB);
            else if (it.dyn == dSpMode) { const int m = (int) std::lrint (v.spMode.load() * 2.0f); t = m <= 0 ? "FLOCK" : (m == 1 ? "FLOCK  +  LORENZ" : (m == 2 ? "LORENZ" : (m == 3 ? "LORENZ  +  GRAVITY" : "GRAVITY"))); }
            if (it.dyn == dLesA || it.dyn == dLesB) g.setColour (Colour (150, 255, 175));
            else if (it.dyn == dLesAn || it.dyn == dLesBn) { g.setColour (Colour (20, 24, 22)); g.fillRect (r); g.setColour (Colour (220, 230, 222)); }
            else g.setColour (it.ink);
            g.setFont (font ((float) it.r.getHeight() + 0.5f));
            g.drawText (t, it.r.expanded (20, 2), juce::Justification::centred, false);
            break;
        }
        default: break;
    }
}

void ObliqPanel::drawControls (juce::Graphics& g)
{
    const bool hidden = anim > 0;
    for (size_t n = 0; n < items.size(); ++n)
    {
        const auto& it = items[n];
        // a page's board (the matrix) is drawn where it sits in the layout: above the main panel, below the page buttons
        if (! hidden && (int) n == pageStart[(size_t) page] && pageImage[(size_t) page].isValid()) g.drawImage (pageImage[(size_t) page], pageBounds[(size_t) page].toFloat());
        if (it.page >= 0 && (it.page != page || hidden)) continue;
        if (it.type == Scope) continue;
        if (it.dyn == dL1 || it.dyn == dL2 || it.dyn == dFol || it.dyn == dOut || it.dyn == dBoid || it.dyn == dLz || it.dyn == dSpd
            || it.dyn == dLesA || it.dyn == dLesB || it.dyn == dSpMode) continue;      // drawn every frame
        drawItem (g, it);
    }
    // the page buttons sit above everything (they are in the matrix board's gutter)
}

void ObliqPanel::drawDynamic (juce::Graphics& g)
{
    auto& v = proc.engine->view;
    const bool hidden = anim > 0;
    const Colour scopeCol (150, 255, 175);
    for (const auto& it : items)
    {
        if (it.page >= 0 && (it.page != page || hidden)) continue;
        const auto r = it.r.toFloat();
        const auto po = it.page >= 0 ? pageBounds[(size_t) it.page].getPosition().toFloat() : juce::Point<float>();
        switch (it.dyn)
        {
            case dL1: g.setOpacity (0.15f + 0.85f * (v.lfo1 * 0.5f + 0.5f)); g.drawImage (it.img, r); break;
            case dL2: g.setOpacity (0.15f + 0.85f * (v.lfo2 * 0.5f + 0.5f)); g.drawImage (it.img, r); break;
            case dFol: g.setOpacity (0.1f + 0.9f * v.follow); g.drawImage (it.img, r); break;
            case dOut: g.setOpacity (0.1f + 0.9f * v.outEnv); g.drawImage (it.img, r); break;
            case dBoid: g.setOpacity (1.0f); g.drawImage (it.img, Rectangle<float> (po.x + 254.0f + (v.boidX[(size_t) it.dynIndex] + 1.0f) * 82.0f, po.y + 23.0f + (v.boidY[(size_t) it.dynIndex] + 1.0f) * 67.0f, 8.0f, 8.0f)); break;
            case dLz: g.setOpacity (it.alpha); g.drawImage (it.img, Rectangle<float> (po.x + 557.0f + juce::jlimit (-1.0f, 1.0f, lzx[(size_t) it.dynIndex]) * 80.0f, po.y + 82.0f + juce::jlimit (-1.0f, 1.0f, lzy[(size_t) it.dynIndex]) * 64.0f, 6.0f, 6.0f)); break;
            case dSpd:
            {
                const float rm = juce::jmax (1.0f, params.get ("spDist")) * 1.2f;
                float qx = v.px[(size_t) it.dynIndex] / rm, qy = v.py[(size_t) it.dynIndex] / rm; const float ql = std::sqrt (qx * qx + qy * qy);
                if (ql > 1.0f) { qx /= ql; qy /= ql; }
                const float sz = juce::jlimit (4.0f, 12.0f, 7.0f + v.pz[(size_t) it.dynIndex] / rm * 6.0f);
                g.setOpacity (1.0f); g.drawImage (it.img, Rectangle<float> (po.x + 450.0f - qy * 92.0f - sz / 2, po.y + 104.0f - qx * 92.0f - sz / 2, sz, sz));
                break;
            }
            case dLesA: case dLesB: case dSpMode: g.setOpacity (1.0f); drawItem (g, it); break;
            default: break;
        }
        g.setOpacity (1.0f);
        if (it.type == Scope)
        {
            g.setColour (scopeCol);
            juce::Path p;
            if (it.signals.size() == 2)
            {   // the polygon (or the Lorenz butterfly) as an XY figure
                if (it.signals[0] == "adispX")
                {
                    const float order = juce::jlimit (2.05f, 32.0f, params.get ("pRegular") > 0.5f ? std::round (params.get ("pOrder")) : params.get ("pOrder"));
                    const float teeth = params.get ("pTeeth"), amt = params.get ("pAmt"), skew = params.get ("pPhase");
                    float ratio = params.get ("pRatio"); if (params.get ("pSnap") > 0.5f) ratio = ratio < 0.75f ? 0.5f : std::round (ratio);
                    const float roll = params.get ("pRoll") + (float) tickCount / 30.0f * params.get ("pSpin");
                    const double pin = juce::MathConstants<double>::pi / order; double tmax = juce::MathConstants<double>::halfPi - pin - 0.07; if (tmax < 0) tmax = 0;
                    const double T = teeth * tmax; const int n = 400; const int turns = (int) std::ceil (order) <= 16 ? 1 : 1;
                    for (int i = 0; i <= n * turns; ++i)
                    {
                        const double ph = (double) i / n, th = ph + amt * std::sin (juce::MathConstants<double>::twoPi * ph * ratio) * 0.3;
                        double fr = th * order; fr -= std::floor (fr);
                        double den = juce::jlimit (0.04, 1.0, std::cos (2 * pin * fr - pin + T));
                        const double P = std::cos (pin + T) / den, ang = juce::MathConstants<double>::twoPi * (th + roll);
                        const float x = r.getCentreX() + (float) (P * std::cos (ang)) * r.getWidth() * 0.46f, y = r.getCentreY() - (float) (P * std::sin (ang + skew * juce::MathConstants<double>::halfPi)) * r.getHeight() * 0.46f;
                        if (i == 0) p.startNewSubPath (x, y); else p.lineTo (x, y);
                    }
                }
            }
            else if (it.signals.size() == 1)
            {
                const auto& h = lfoH[it.signals[0] == "alfo1" ? 0 : 1];
                for (size_t i = 0; i < h.size(); ++i)
                {
                    const float x = r.getX() + r.getWidth() * (float) i / (float) (h.size() - 1), y = r.getCentreY() - h[i] * r.getHeight() * 0.45f;
                    if (i == 0) p.startNewSubPath (x, y); else p.lineTo (x, y);
                }
            }
            g.saveState(); g.reduceClipRegion (it.r); g.strokePath (p, juce::PathStrokeType (1.2f)); g.restoreState();
        }
    }
    // value read-out while hovering or dragging
    const int ti = dragItem >= 0 ? dragItem : hoverItem;
    if (ti >= 0 && items[(size_t) ti].param >= 0 && (items[(size_t) ti].type == Knob || items[(size_t) ti].type == VSlider))
    {
        const auto& it = items[(size_t) ti];
        const String t = (it.popup.isNotEmpty() ? it.popup : it.channel) + ":  " + String (params.get (it.param), 3);
        auto font = face != nullptr ? juce::Font (juce::FontOptions (face).withHeight (11.0f)) : juce::Font (juce::FontOptions (11.0f));
        const float w = juce::GlyphArrangement::getStringWidth (font, t) + 12.0f;
        Rectangle<float> box (juce::jlimit (2.0f, (float) baseW - w - 2.0f, (float) it.r.getCentreX() - w / 2), (float) it.r.getY() - 20.0f < 2.0f ? (float) it.r.getBottom() + 4.0f : (float) it.r.getY() - 20.0f, w, 16.0f);
        g.setColour (juce::Colours::white); g.fillRect (box); g.setColour (juce::Colours::black); g.drawRect (box, 1.0f);
        g.setFont (font); g.drawText (t, box, juce::Justification::centred);
    }
}

void ObliqPanel::paint (juce::Graphics& g)
{
    g.setImageResamplingQuality (juce::Graphics::lowResamplingQuality);       // crisp pixels, and fast
    g.addTransform (juce::AffineTransform::scale (scale));
    if (bg.isValid()) g.drawImage (bg, Rectangle<float> (0, 0, (float) baseW, (float) baseH)); else g.fillAll (Colour (60, 64, 62));

    // the controls are cached at device resolution and only redrawn when something changes
    const float ds = scale * (float) g.getInternalContext().getPhysicalPixelScaleFactor() / scale;
    const float ps = juce::jmax (1.0f, (float) g.getInternalContext().getPhysicalPixelScaleFactor());
    juce::ignoreUnused (ds);
    const bool hidden = anim > 0;
    const int change = params.changeCount.load() * 4 + proc.engine->view.sampler.load();
    if (! layer.isValid() || layerChange != change || layerPage != page || layerScale != ps || layerHidden != hidden)
    {
        layerChange = change; layerPage = page; layerScale = ps; layerHidden = hidden;
        const int w = (int) std::ceil (baseW * ps), h = (int) std::ceil (baseH * ps);
        if (! layer.isValid() || layer.getWidth() != w || layer.getHeight() != h) layer = juce::Image (juce::Image::ARGB, w, h, true);
        else layer.clear (layer.getBounds());
        juce::Graphics lg (layer);
        lg.setImageResamplingQuality (juce::Graphics::lowResamplingQuality);
        lg.addTransform (juce::AffineTransform::scale (ps / scale));
        lg.addTransform (juce::AffineTransform::scale (scale));
        drawControls (lg);
    }
    g.drawImage (layer, Rectangle<float> (0, 0, (float) baseW, (float) baseH));
    drawDynamic (g);
    if (helpOpen) drawHelp (g);
}

// =================================================================================================== interaction
int ObliqPanel::hit (juce::Point<float> p) const
{
    if (anim > 0) return -1;
    for (int i = (int) items.size() - 1; i >= 0; --i)
    {
        const auto& it = items[(size_t) i];
        if (it.type == Image || it.type == Label || it.type == Scope) continue;
        if (it.page >= 0 && it.page != page) continue;
        // controls under a page's board can't be reached
        if (it.page < 0 && i < pageStart[(size_t) page] && pageImage[(size_t) page].isValid() && pageBounds[(size_t) page].toFloat().contains (p)) continue;
        if (it.r.toFloat().contains (p)) return i;
    }
    return -1;
}

void ObliqPanel::setParam (int item, float norm)
{
    const auto& it = items[(size_t) item];
    if (it.param >= 0) params.set (it.param, params.fromNorm (it.param, norm));
}

void ObliqPanel::showMenu (int item)
{
    auto& it = items[(size_t) item];
    juce::PopupMenu m;
    auto area = localAreaToGlobal ((it.r.toFloat() * scale).toNearestInt());
    juce::Component::SafePointer<ObliqPanel> safe (this);
    if (it.type == PresetBox)
    {
        const auto names = proc.presetNames();
        for (int i = 0; i < names.size(); ++i) m.addItem (i + 1, names[i], true, names[i] == proc.currentPreset);
        m.showMenuAsync (juce::PopupMenu::Options().withTargetScreenArea (area).withMaximumNumColumns (4), [safe, names] (int r) { if (safe != nullptr && r > 0) safe->proc.loadPreset (names[r - 1]); });
    }
    else if (it.type == SizeBox)
    {
        const float sizes[] = { 0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f };
        for (int i = 0; i < 6; ++i) m.addItem (i + 1, it.text[i], true, std::abs (sizes[i] - scale) < 0.01f);
        if (OBLIQ_SONIC)
        {
            m.addSeparator();
            m.addItem (100, "Output: stereo (decoded from the Ambisonics)", true, proc.stereoMonitor.load());
            m.addItem (101, "Output: 16-channel Ambisonics (ACN / SN3D)", true, ! proc.stereoMonitor.load());
        }
        m.showMenuAsync (juce::PopupMenu::Options().withTargetScreenArea (area), [safe] (int r)
        {
            const float sz[] = { 0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f };
            if (safe == nullptr || r <= 0) return;
            if (r >= 100) safe->proc.stereoMonitor = r == 100;
            else if (safe->onScale) safe->onScale (sz[r - 1]);
        });
    }
    else
    {
        const int cur = (int) std::lrint (params.get (it.param));
        for (int i = 0; i < it.text.size(); ++i) m.addItem (i + 1, it.text[i], true, cur == i + 1);
        const int pi = it.param;
        m.showMenuAsync (juce::PopupMenu::Options().withTargetScreenArea (area), [safe, pi] (int r) { if (safe != nullptr && r > 0) safe->params.set (pi, (float) r); });
    }
}

void ObliqPanel::mouseDown (const juce::MouseEvent& e)
{
    grabKeyboardFocus();
    const auto p = toPanel (e.position);
    if (helpOpen) { if (! helpClick (p)) helpOpen = false; return; }
    const int i = hit (p);
    if (i < 0) return;
    auto& it = items[(size_t) i];
    switch (it.type)
    {
        case Knob: case VSlider: case NSlider:
            dragItem = i; dragStart = params.toNorm (it.param, params.get (it.param)); dragPos = p; break;
        case Check:
            if (it.group.isNotEmpty())
            {
                for (auto& o : items) if (o.type == Check && o.group == it.group && o.param >= 0) params.set (o.param, 0.0f);
                params.set (it.param, 1.0f);
            }
            else if (it.channel == "lRnd")
            {   // randomize both filters
                auto roll = [this] (const char* n) { const int k = params.find (n); if (k >= 0) params.set (k, params.fromNorm (k, random.nextFloat())); };
                for (auto n : { "aMode", "aGain", "LPFreq", "Res", "bCut", "bRes", "bMode", "bGain", "lMix" }) roll (n);
                params.set ("link", (float) (1 + random.nextInt (5)));
            }
            else params.set (it.param, params.get (it.param) > 0.5f ? 0.0f : 1.0f);
            break;
        case Combo: case PresetBox: case SizeBox: showMenu (i); break;
        case Button: params.set (it.param, params.get (it.param) + 1.0f); break;
        case PresetSave:
        {
            auto* aw = new juce::AlertWindow ("Save preset", "Name:", juce::MessageBoxIconType::NoIcon);
            aw->addTextEditor ("name", proc.currentPreset == "Default" ? String ("My sound") : proc.currentPreset);
            aw->addButton ("Save", 1, juce::KeyPress (juce::KeyPress::returnKey)); aw->addButton ("Cancel", 0, juce::KeyPress (juce::KeyPress::escapeKey));
            juce::Component::SafePointer<ObliqPanel> safe (this);
            aw->enterModalState (true, juce::ModalCallbackFunction::create ([safe, aw] (int r) { if (safe != nullptr && r == 1) { auto n = aw->getTextEditorContents ("name").trim(); if (n.isNotEmpty()) safe->proc.savePreset (n); } }), true);
            break;
        }
        case PresetRemove: proc.removePreset (proc.currentPreset); break;
        case Help: helpOpen = true; dragItem = -1; break;
        default: break;
    }
}

void ObliqPanel::mouseDrag (const juce::MouseEvent& e)
{
    if (dragItem < 0) return;
    const auto p = toPanel (e.position);
    const float range = e.mods.isShiftDown() ? 800.0f : 180.0f;
    setParam (dragItem, juce::jlimit (0.0f, 1.0f, dragStart + (dragPos.y - p.y) / range));
}

void ObliqPanel::mouseUp (const juce::MouseEvent&) { dragItem = -1; }
void ObliqPanel::mouseMove (const juce::MouseEvent& e) { mousePos = toPanel (e.position); hoverItem = helpOpen ? -1 : hit (mousePos); }
void ObliqPanel::mouseExit (const juce::MouseEvent&) { hoverItem = -1; }

void ObliqPanel::mouseDoubleClick (const juce::MouseEvent& e)
{
    if (helpOpen) return;
    const int i = hit (toPanel (e.position));
    if (i >= 0 && items[(size_t) i].param >= 0 && (items[(size_t) i].type == Knob || items[(size_t) i].type == VSlider || items[(size_t) i].type == NSlider))
        params.set (items[(size_t) i].param, params.def (items[(size_t) i].param).def);
}

void ObliqPanel::mouseWheelMove (const juce::MouseEvent& e, const juce::MouseWheelDetails& w)
{
    if (helpOpen) return;
    const int i = hit (toPanel (e.position));
    if (i >= 0 && items[(size_t) i].param >= 0 && (items[(size_t) i].type == Knob || items[(size_t) i].type == VSlider || items[(size_t) i].type == NSlider))
        setParam (i, juce::jlimit (0.0f, 1.0f, params.toNorm (items[(size_t) i].param, params.get (items[(size_t) i].param)) + w.deltaY * 0.15f));
}

// the computer keyboard plays notes: A W S E D F T G Y H U J K O L P ; '   (Z / X octave, C / V velocity)
bool ObliqPanel::keyPressed (const juce::KeyPress& k)
{
    if (k == juce::KeyPress::F1Key) { helpOpen = ! helpOpen; return true; }
    if (helpOpen && k == juce::KeyPress::escapeKey) { helpOpen = false; return true; }
    if (helpOpen && (k == juce::KeyPress::upKey || k == juce::KeyPress::downKey))
    {
        const int n = (int) helpTopics().size();
        helpTopic = (helpTopic + (k == juce::KeyPress::downKey ? 1 : n - 1)) % n; return true;
    }
    const auto c = juce::CharacterFunctions::toLowerCase (k.getTextCharacter());
    if (c == 'z') { kbOctave = juce::jmax (-3, kbOctave - 1); return true; }
    if (c == 'x') { kbOctave = juce::jmin (4, kbOctave + 1); return true; }
    if (c == 'c') { kbVelocity = juce::jmax (10, kbVelocity - 20); return true; }
    if (c == 'v') { kbVelocity = juce::jmin (127, kbVelocity + 20); return true; }
    return String (kKeys).containsChar (c);
}

bool ObliqPanel::keyStateChanged (bool)
{
    bool used = false;
    for (int i = 0; kKeys[i] != 0; ++i)
    {
        const bool down = juce::KeyPress::isKeyCurrentlyDown (kKeys[i]) && ! juce::ModifierKeys::currentModifiers.isCommandDown();
        const bool was = heldKeys.count (i) > 0;
        if (down && ! was) { const int n = juce::jlimit (0, 127, 60 + 12 * kbOctave + i); heldKeys[i] = n; proc.keyboard.noteOn (1, n, (float) kbVelocity / 127.0f); used = true; }
        else if (! down && was) { proc.keyboard.noteOff (1, heldKeys[i], 0.0f); heldKeys.erase (i); used = true; }
    }
    return used;
}

// =================================================================================================== help
std::vector<int> ObliqPanel::helpTopics() const
{
    std::vector<int> t;
    for (int i = 0; i < (int) (sizeof (kHelp) / sizeof (kHelp[0])); ++i) if (OBLIQ_SONIC || ! kHelp[i].sonicOnly) t.push_back (i);
    return t;
}

namespace
{
    void bevel (juce::Graphics& g, Rectangle<float> r, bool raised)
    {
        g.setColour (raised ? juce::Colours::white : Colour (70, 74, 70)); g.fillRect (r.getX(), r.getY(), r.getWidth(), 1.0f); g.fillRect (r.getX(), r.getY(), 1.0f, r.getHeight());
        g.setColour (raised ? Colour (70, 74, 70) : juce::Colours::white); g.fillRect (r.getX(), r.getBottom() - 1.0f, r.getWidth(), 1.0f); g.fillRect (r.getRight() - 1.0f, r.getY(), 1.0f, r.getHeight());
    }
    Rectangle<float> helpTopicRect (Rectangle<float> w, int i) { return { w.getX() + 10.0f, w.getY() + 34.0f + (float) i * 26.0f, 118.0f, 22.0f }; }
    Rectangle<float> helpCloseRect (Rectangle<float> w) { return { w.getRight() - 21.0f, w.getY() + 5.0f, 16.0f, 14.0f }; }
    Rectangle<float> helpManualRect (Rectangle<float> w) { return { w.getX() + 10.0f, w.getBottom() - 34.0f, 118.0f, 22.0f }; }
}

void ObliqPanel::drawHelp (juce::Graphics& g)
{
    auto bold = [&] (float h) { return face != nullptr ? juce::Font (juce::FontOptions (face).withHeight (h)) : juce::Font (juce::FontOptions (h, juce::Font::bold)); };
    const juce::Font plain (juce::FontOptions ("Tahoma", 12.5f, juce::Font::plain));
    const auto w = helpWindow();
    const auto topics = helpTopics();
    helpTopic = juce::jlimit (0, (int) topics.size() - 1, helpTopic);

    g.setColour (Colour (0x70081610)); g.fillRect (0, 0, baseW, baseH);
    g.setColour (Colour (0x50000000)); g.fillRect (w.translated (4.0f, 4.0f));
    g.setColour (Colour (200, 204, 200)); g.fillRect (w); g.setColour (juce::Colours::black); g.drawRect (w.expanded (1.0f), 1.0f); bevel (g, w, true);

    // title bar
    const Rectangle<float> bar (w.getX() + 3.0f, w.getY() + 3.0f, w.getWidth() - 6.0f, 18.0f);
    g.setGradientFill (juce::ColourGradient (Colour (34, 78, 52), bar.getX(), 0.0f, Colour (115, 174, 138), bar.getRight(), 0.0f, false)); g.fillRect (bar);
    g.setColour (juce::Colours::white); g.setFont (bold (12.0f));
    g.drawText (String (JucePlugin_Name) + " Help", bar.reduced (6.0f, 0.0f), juce::Justification::centredLeft);
    const auto cl = helpCloseRect (w);
    g.setColour (Colour (200, 204, 200)); g.fillRect (cl); bevel (g, cl, true);
    g.setColour (juce::Colours::black); g.drawLine (cl.getX() + 4.5f, cl.getY() + 3.5f, cl.getRight() - 4.5f, cl.getBottom() - 3.5f, 1.6f); g.drawLine (cl.getRight() - 4.5f, cl.getY() + 3.5f, cl.getX() + 4.5f, cl.getBottom() - 3.5f, 1.6f);

    // topics
    for (int i = 0; i < (int) topics.size(); ++i)
    {
        const auto r = helpTopicRect (w, i); const bool on = i == helpTopic;
        g.setColour (on ? Colour (115, 174, 138) : Colour (200, 204, 200)); g.fillRect (r); bevel (g, r, ! on);
        g.setColour (juce::Colours::black); g.setFont (bold (11.0f)); g.drawText (kHelp[topics[(size_t) i]].title, r.translated (on ? 1.0f : 0.0f, on ? 1.0f : 0.0f), juce::Justification::centred);
    }
    const auto mr = helpManualRect (w);
    g.setColour (Colour (200, 204, 200)); g.fillRect (mr); bevel (g, mr, true);
    g.setColour (juce::Colours::black); g.setFont (bold (11.0f)); g.drawText ("Manual (PDF)", mr, juce::Justification::centred);

    // text
    const Rectangle<float> box (w.getX() + 138.0f, w.getY() + 34.0f, w.getWidth() - 148.0f, w.getHeight() - 46.0f);
    g.setColour (juce::Colours::white); g.fillRect (box); bevel (g, box, false);
    juce::AttributedString as; as.setWordWrap (juce::AttributedString::byWord); as.setLineSpacing (1.5f);
    juce::StringArray lines; lines.addLines (kHelp[topics[(size_t) helpTopic]].body);
    bool first = true;
    for (auto& l : lines)
    {
        if (l.startsWith ("# ")) { if (! first) as.append ("\n", juce::Font (juce::FontOptions (5.0f)), juce::Colours::black); as.append (l.substring (2).toUpperCase() + "\n", bold (12.0f), Colour (34, 96, 58)); }
        else as.append (l + "\n", plain, Colour (8, 22, 14));
        first = false;
    }
    as.draw (g, box.reduced (12.0f, 9.0f));
}

bool ObliqPanel::helpClick (juce::Point<float> p)
{
    const auto w = helpWindow();
    if (! w.contains (p) || helpCloseRect (w).contains (p)) return false;
    const int n = (int) helpTopics().size();
    for (int i = 0; i < n; ++i) if (helpTopicRect (w, i).contains (p)) helpTopic = i;
    if (helpManualRect (w).contains (p))
    {
        auto pdf = ObliqProcessor::resourceDir().getChildFile ("ObliqSound_ObliqSonic_Manual.pdf");
        if (pdf.existsAsFile()) pdf.startAsProcess(); else juce::URL ("https://github.com/femifleming/obliqsound").launchInDefaultBrowser();
    }
    return true;
}

// =================================================================================================== editor
ObliqEditor::ObliqEditor (ObliqProcessor& p) : AudioProcessorEditor (p), panel (p)
{
    addAndMakeVisible (panel);
    panel.onScale = [this] (float s) { panel.scale = s; setSize ((int) std::lrint (panel.baseW * s), (int) std::lrint (panel.baseH * s)); };
    setResizable (false, false);
    setSize (panel.baseW, panel.baseH);
}

void ObliqEditor::resized() { panel.setBounds (getLocalBounds()); }
