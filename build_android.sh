#!/bin/bash
# Build script for Belinda AI Android APK using Kivy/Buildozer
# This version handles paths with spaces and recognizes both APK and AAB outputs.

# Set the final output directory on the Windows side
BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
ANDROID_DIST_DIR="$BASE_OUTPUT_DIR/android"

# Temporary build directory in WSL (NO SPACES ALLOWED)
BUILD_WORK_DIR="/root/belinda_android_build"

echo "--- Installing/Updating System Dependencies ---"
sudo pacman -S --noconfirm git jdk17-openjdk zip unzip autoconf libtool pkg-config

# Detect if we are in a virtualenv
if [ -n "$VIRTUAL_ENV" ]; then
    PIP_CMD="pip"
else
    PIP_CMD="pip install --user"
fi

echo "--- Installing Buildozer (Latest Git) ---"
$PIP_CMD install git+https://github.com/kivy/buildozer.git@master cython

# --- Aggressive Patch for Python 3.14 compatibility ---
VENV_LIB=$(python -c "import site; print(site.getsitepackages()[0])")
INIT_FILE="$VENV_LIB/buildozer/__init__.py"
if [ -f "$INIT_FILE" ]; then
    echo "--- Patching buildozer for Python 3.14 compatibility ---"
    sed -i "s/from urllib.request import FancyURLopener/# from urllib.request import FancyURLopener/g" "$INIT_FILE"
    python -c "
import os
path = '$INIT_FILE'
with open(path, 'r') as f: lines = f.readlines()
with open(path, 'w') as f:
    skip = False
    for line in lines:
        if 'class ChromeDownloader' in line: skip = True
        if skip and line.strip() == '': skip = False; continue
        if not skip: f.write(line)
"
fi

echo "--- Preparing Temporary Build Workspace ---"
rm -rf "$BUILD_WORK_DIR"
mkdir -p "$BUILD_WORK_DIR"
cp -r . "$BUILD_WORK_DIR/"
cd "$BUILD_WORK_DIR"

echo "--- Starting Android Build in $BUILD_WORK_DIR ---"
# Use 'debug' instead of 'release' to ensure we get an installable .apk file
buildozer --allow-root android debug

# Find the generated package (could be .apk or .aab)
PKG_FILE=$(find bin/ -name "*.apk" -o -name "*.aab" | head -n 1)

if [ -f "$PKG_FILE" ]; then
    echo "--- Build successful! ---"
    mkdir -p "$ANDROID_DIST_DIR"
    cp "$PKG_FILE" "$ANDROID_DIST_DIR/"
    echo "Package available at: $ANDROID_DIST_DIR/$(basename $PKG_FILE)"
else
    echo "--- Build failed! ---"
    echo "Check the buildozer logs above."
    exit 1
fi

cd - > /dev/null
