cmake_minimum_required(VERSION 3.22)
project(Obliq VERSION 2.0.0)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 11.0)
if(DEFINED ENV{JUCE_DIR})
  set(JUCE_DIR $ENV{JUCE_DIR})
else()
  set(JUCE_DIR $ENV{HOME}/cassetter-plugin/JUCE)
endif()
add_subdirectory(${JUCE_DIR} ${CMAKE_BINARY_DIR}/juce)

# ---- the embedded SuperCollider server (built by third_party/sc-build; see sc/build_sc.sh)
set(SC ${CMAKE_SOURCE_DIR}/../third_party/supercollider)
set(SCB ${CMAKE_SOURCE_DIR}/../third_party/sc-build)
add_library(scengine STATIC ../sc/ScEngine.cpp)
set_target_properties(scengine PROPERTIES CXX_STANDARD 17 POSITION_INDEPENDENT_CODE ON)
target_compile_definitions(scengine PRIVATE BOOST_CHRONO_HEADER_ONLY BOOST_CONFIG_SUPPRESS_OUTDATED_MESSAGE NOVA_SIMD NO_LIBSNDFILE SC_FFT_VDSP SC_MEMORY_ALIGNMENT=32)
target_compile_options(scengine PRIVATE -w)
target_include_directories(scengine PRIVATE ${SCB}/common ${SC}/external_libraries ${SC}/external_libraries/nova-simd ${SC}/external_libraries/nova-tt
    ${SC}/external_libraries/boost ${SC}/include/common ${SC}/common ${SC}/include/server ${SC}/include/plugin_interface ${SC}/server/scsynth
    ${SC}/external_libraries/boost_sync/include ${SC}/external_libraries/TLSF-2.4.6/src)
target_link_libraries(scengine PUBLIC ${SCB}/server/scsynth/libscsynth.a ${SCB}/external_libraries/libtlsf.a
    ${SCB}/external_libraries/libboost_filesystem_lib.a ${SCB}/external_libraries/libboost_system_lib.a
    "-framework CoreAudio" "-framework CoreServices" "-framework Accelerate" "-framework Foundation" "-framework AppKit" "-framework AudioToolbox")

function(obliq name sonic code icon)
  juce_add_plugin(${name}
      COMPANY_NAME "ObliqSound" BUNDLE_ID com.obliqsound.${name} PRODUCT_NAME "${name}"
      PLUGIN_MANUFACTURER_CODE Oblq PLUGIN_CODE ${code}
      IS_SYNTH TRUE NEEDS_MIDI_INPUT TRUE NEEDS_MIDI_OUTPUT FALSE IS_MIDI_EFFECT FALSE EDITOR_WANTS_KEYBOARD_FOCUS TRUE
      FORMATS VST3 AU Standalone COPY_PLUGIN_AFTER_BUILD FALSE
      VST3_CATEGORIES Instrument Synth AU_MAIN_TYPE kAudioUnitType_MusicDevice
      ICON_BIG ${CMAKE_SOURCE_DIR}/../app/${icon}
      MICROPHONE_PERMISSION_ENABLED FALSE)
  target_sources(${name} PRIVATE Source/PluginProcessor.cpp Source/PluginEditor.cpp Source/Engine.cpp)
  target_compile_definitions(${name} PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0 JUCE_DISPLAY_SPLASH_SCREEN=0
      JUCE_REPORT_APP_USAGE=0 JUCE_MODAL_LOOPS_PERMITTED=0 OBLIQ_SONIC=${sonic})
  target_link_libraries(${name} PRIVATE scengine juce::juce_audio_utils juce::juce_audio_formats
      PUBLIC juce::juce_recommended_config_flags juce::juce_recommended_lto_flags)
endfunction()

obliq(ObliqSound 0 Obsd icon.png)
obliq(ObliqSonic 1 Obsc icon_sonic.png)
