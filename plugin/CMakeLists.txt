cmake_minimum_required(VERSION 3.22)
set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 11.0)
project(Obliq VERSION 2.2.1)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(MSVC)
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")   # as SuperCollider is built
endif()
if(DEFINED ENV{JUCE_DIR})
  set(JUCE_DIR $ENV{JUCE_DIR})
else()
  set(JUCE_DIR $ENV{HOME}/cassetter-plugin/JUCE)
endif()
add_subdirectory(${JUCE_DIR} ${CMAKE_BINARY_DIR}/juce)

# ---- the embedded SuperCollider server (built by sc/fetch_sc.sh into third_party/sc-build)
set(SC ${CMAKE_SOURCE_DIR}/../third_party/supercollider)
set(SCB ${CMAKE_SOURCE_DIR}/../third_party/sc-build)
set(SC_INCLUDES ${SCB}/common ${SC}/external_libraries ${SC}/external_libraries/nova-simd ${SC}/external_libraries/nova-tt
    ${SC}/external_libraries/boost ${SC}/include/common ${SC}/common ${SC}/include/server ${SC}/include/plugin_interface ${SC}/server/scsynth
    ${SC}/external_libraries/boost_sync/include ${SC}/external_libraries/TLSF-2.4.6/src)
set(SC_DEFS BOOST_CHRONO_HEADER_ONLY BOOST_CONFIG_SUPPRESS_OUTDATED_MESSAGE NOVA_SIMD NO_LIBSNDFILE SC_MEMORY_ALIGNMENT=32)
if(APPLE)
  list(APPEND SC_DEFS SC_FFT_VDSP)
elseif(WIN32)
  list(APPEND SC_DEFS SC_FFT_GREEN WIN32_LEAN_AND_MEAN NOMINMAX _WIN32_WINNT=0x0600 BOOST_ALL_NO_LIB _USE_MATH_DEFINES _ENABLE_ATOMIC_ALIGNMENT_FIX _CRT_SECURE_NO_WARNINGS _SCL_SECURE_NO_WARNINGS)
else()
  list(APPEND SC_DEFS SC_FFT_GREEN SC_AUDIO_API=2)       # 2 = JACK in SC_CoreAudio.h; its back end is not linked
endif()
# the static libraries of the SuperCollider build, wherever the generator put them
function(sc_lib var)
  set(found "")
  foreach(pat ${ARGN})
    file(GLOB_RECURSE hit ${SCB}/${pat})
    if(hit)
      list(GET hit 0 found)
      break()
    endif()
  endforeach()
  if(NOT found)
    message(FATAL_ERROR "SuperCollider library not found (${ARGN}): run sc/fetch_sc.sh first")
  endif()
  set(${var} ${found} PARENT_SCOPE)
endfunction()
sc_lib(LIB_SCSYNTH server/scsynth/libscsynth.a server/scsynth/libscsynth.lib server/scsynth/*scsynth*.lib)
sc_lib(LIB_TLSF external_libraries/libtlsf.a external_libraries/tlsf.lib external_libraries/*tlsf*.lib)
sc_lib(LIB_BFS external_libraries/libboost_filesystem_lib.a external_libraries/boost_filesystem_lib.lib external_libraries/*boost_filesystem*.lib)
sc_lib(LIB_BSYS external_libraries/libboost_system_lib.a external_libraries/boost_system_lib.lib external_libraries/*boost_system*.lib)

add_library(scengine STATIC ../sc/ScEngine.cpp)
set_target_properties(scengine PROPERTIES CXX_STANDARD 17 POSITION_INDEPENDENT_CODE ON)
target_compile_definitions(scengine PRIVATE ${SC_DEFS})
target_compile_options(scengine PRIVATE $<IF:$<CXX_COMPILER_ID:MSVC>,/w,-w>)
target_include_directories(scengine PRIVATE ${SC_INCLUDES})
target_link_libraries(scengine PUBLIC ${LIB_SCSYNTH} ${LIB_TLSF} ${LIB_BFS} ${LIB_BSYS})
if(APPLE)
  target_link_libraries(scengine PUBLIC "-framework CoreAudio" "-framework CoreServices" "-framework Accelerate" "-framework Foundation" "-framework AppKit" "-framework AudioToolbox")
elseif(WIN32)
  target_link_libraries(scengine PUBLIC ws2_32 winmm iphlpapi)
else()
  target_link_libraries(scengine PUBLIC pthread dl)
endif()

# ---- our UGens, as a server plug-in (.scx; .so on Linux, as the server expects there)
add_library(OblqUGens MODULE ../sc/ugens/OblqUGens.cpp)
set_target_properties(OblqUGens PROPERTIES CXX_STANDARD 17 PREFIX "" CXX_VISIBILITY_PRESET hidden POSITION_INDEPENDENT_CODE ON)
if(APPLE OR WIN32)
  set_target_properties(OblqUGens PROPERTIES SUFFIX ".scx")
endif()
target_compile_definitions(OblqUGens PRIVATE ${SC_DEFS})
target_compile_options(OblqUGens PRIVATE $<IF:$<CXX_COMPILER_ID:MSVC>,/w,-w>)
target_include_directories(OblqUGens PRIVATE ${SC_INCLUDES})

# On Windows SuperCollider's own UGen targets drag in its language interpreter, so the stock UGens we use
# are built here from its sources instead (one file each).
if(WIN32)
  foreach(p BinaryOpUGens UnaryOpUGens MulAddUGens IOUGens OscUGens LFUGens NoiseUGens DynNoiseUGens FilterUGens DelayUGens
            PanUGens TriggerUGens ReverbUGens GrainUGens ChaosUGens DemandUGens PhysicalModelingUGens)
    add_library(${p} MODULE ${SC}/server/plugins/${p}.cpp)
    set_target_properties(${p} PROPERTIES CXX_STANDARD 17 PREFIX "" SUFFIX ".scx" LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/scplugins)
    target_compile_definitions(${p} PRIVATE ${SC_DEFS})
    target_compile_options(${p} PRIVATE /w /Zc:__cplusplus)
    target_include_directories(${p} PRIVATE ${SC_INCLUDES})
    target_link_libraries(${p} PRIVATE wsock32 ws2_32)
  endforeach()
endif()

# ---- engine smoke test: starts the server, loads the SynthDefs, plays 16 voices, checks the output
add_executable(obliq_smoke ../sc/voicetest.cpp)
set_target_properties(obliq_smoke PROPERTIES CXX_STANDARD 17)
target_link_libraries(obliq_smoke PRIVATE scengine)

if(APPLE)
  set(OBLIQ_FORMATS VST3 AU Standalone)
else()
  set(OBLIQ_FORMATS VST3 Standalone)
endif()

function(obliq name sonic code icon)
  juce_add_plugin(${name}
      COMPANY_NAME "ObliqSound" BUNDLE_ID com.obliqsound.${name} PRODUCT_NAME "${name}"
      PLUGIN_MANUFACTURER_CODE Oblq PLUGIN_CODE ${code}
      IS_SYNTH TRUE NEEDS_MIDI_INPUT TRUE NEEDS_MIDI_OUTPUT FALSE IS_MIDI_EFFECT FALSE EDITOR_WANTS_KEYBOARD_FOCUS TRUE
      FORMATS ${OBLIQ_FORMATS} COPY_PLUGIN_AFTER_BUILD FALSE
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
