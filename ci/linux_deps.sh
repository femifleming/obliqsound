#!/bin/bash
# Build dependencies for Ubuntu / Debian (SuperCollider server + JUCE).
set -e
export DEBIAN_FRONTEND=noninteractive
SUDO=$([ "$(id -u)" = 0 ] || echo sudo)
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq build-essential git cmake ninja-build pkg-config python3 zip unzip \
  libjack-jackd2-dev libasound2-dev libudev-dev \
  libx11-dev libxext-dev libxrandr-dev libxinerama-dev libxcursor-dev libxcomposite-dev libxrender-dev libxi-dev libxtst-dev \
  libfreetype6-dev libfontconfig1-dev libgl1-mesa-dev libcurl4-openssl-dev
