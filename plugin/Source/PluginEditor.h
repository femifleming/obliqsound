#pragma once
#include "PluginProcessor.h"
#include <juce_gui_basics/juce_gui_basics.h>

// The whole panel is one component that draws itself from layout.json (written by gen.py + export_layout.py):
// the same art, positions and pages as before, but a single paint instead of 1500 widgets.
class ObliqPanel : public juce::Component, private juce::Timer
{
public:
    explicit ObliqPanel (ObliqProcessor&);
    ~ObliqPanel() override;
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;
    void mouseDoubleClick (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    bool keyPressed (const juce::KeyPress&) override;
    bool keyStateChanged (bool) override;
    int baseW = 960, baseH = 630;
    std::function<void (float)> onScale;
    float scale = 1.0f;

private:
    enum Type { Image, Knob, VSlider, NSlider, Check, Combo, Button, Label, Scope, PresetBox, PresetSave, PresetRemove, SizeBox };
    struct Item
    {
        Type type = Image; juce::Rectangle<int> r; int page = -1; int param = -1;
        juce::String channel, file, popup; juce::StringArray text; juce::Image img, img2;
        int frames = 1; float alpha = 1.0f; bool visible = true; juce::Colour ink { 8, 22, 14 }; juce::String group; int align = 0;
        int dyn = 0, dynIndex = 0;        // engine-driven behaviour
        juce::StringArray signals;
    };
    void timerCallback() override;
    void build();
    juce::Image art (const juce::String& file);
    int hit (juce::Point<float>) const;
    void drawItem (juce::Graphics&, const Item&);
    void drawControls (juce::Graphics&);
    void drawDynamic (juce::Graphics&);
    void setParam (int item, float norm);
    void showMenu (int item);
    void changePage (int to);
    juce::String bgName (int page, int morph, int idle) const;
    juce::Point<float> toPanel (juce::Point<float> p) const { return p / scale; }

    ObliqProcessor& proc;
    ParamStore& params;
    std::vector<Item> items;
    juce::StringArray pageNames;                      // container channels, in tab order
    std::vector<juce::Rectangle<int>> pageBounds; std::vector<juce::Image> pageImage; std::vector<int> pageStart;
    std::vector<int> tabParams;
    juce::Typeface::Ptr face;
    juce::File artDir;
    juce::String prefix;

    // pages / background
    int page = 0, fromPage = 0, anim = 0, idle = 0, idleDir = 1, pending = -1, tickCount = 0;
    enum { kNfr = 6, kNidle = 120 };
    juce::Image bg;
    juce::Image layer; int layerChange = -1, layerPage = -1; float layerScale = 0; bool layerHidden = false;

    // interaction
    int dragItem = -1, hoverItem = -1; float dragStart = 0; juce::Point<float> dragPos, mousePos;
    juce::Random random;
    std::array<float, 24> lzx {}, lzy {};
    std::vector<float> lfoH[2];
    int lastPresetVersion = -1;
    std::map<int, int> heldKeys; int kbOctave = 0, kbVelocity = 100;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ObliqPanel)
};

class ObliqEditor : public juce::AudioProcessorEditor
{
public:
    explicit ObliqEditor (ObliqProcessor&);
    void resized() override;
    void paint (juce::Graphics& g) override { g.fillAll (juce::Colour (60, 64, 62)); }
private:
    ObliqPanel panel;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ObliqEditor)
};
