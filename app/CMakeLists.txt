cmake_minimum_required(VERSION 3.22)
project(ObliqApps VERSION 1.0)
set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 11.0)
if(DEFINED ENV{JUCE_DIR})
  set(JUCE_DIR $ENV{JUCE_DIR})
else()
  set(JUCE_DIR $ENV{HOME}/cassetter-plugin/JUCE)   # any JUCE 7/8 checkout
endif()
add_subdirectory(${JUCE_DIR} ${CMAKE_BINARY_DIR}/juce)

function(obliq_app target name sonic bundle icon)
  juce_add_gui_app(${target} PRODUCT_NAME "${name}" COMPANY_NAME "ObliqSound"
      BUNDLE_ID ${bundle} ICON_BIG ${CMAKE_SOURCE_DIR}/${icon}
      MICROPHONE_PERMISSION_ENABLED TRUE MICROPHONE_PERMISSION_TEXT "${name} can use audio input."
      VERSION 1.0)
  target_sources(${target} PRIVATE App.mm)
  target_compile_definitions(${target} PRIVATE JUCE_PLUGINHOST_VST3=1 JUCE_PLUGINHOST_AU=0
      JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_APPLICATION_NAME_STRING="${name}" JUCE_APPLICATION_VERSION_STRING="1.0"
      OBLIQ_NAME="${name}" OBLIQ_SONIC=${sonic})
  target_link_libraries(${target} PRIVATE juce::juce_audio_utils PUBLIC juce::juce_recommended_config_flags)
  target_link_libraries(${target} PRIVATE "-framework AppKit")
endfunction()

obliq_app(ObliqSoundApp ObliqSound 0 com.obliqsound.app icon.png)
obliq_app(ObliqSonicApp ObliqSonic 1 com.obliqsound.sonic.app icon_sonic.png)
