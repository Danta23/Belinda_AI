#!/bin/bash
# ULTRA-FAST Build Script for Belinda AI Manager (v2 - Fixed Path Length Error)
# Uses persistent caching, multi-core acceleration, and smart sync.

BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
ANDROID_DIST_DIR="$BASE_OUTPUT_DIR/android"
BUILD_WORK_DIR="/root/belinda_android_build"

# 1. Multi-Core Acceleration (Use all available CPU cores)
export P4A_NUM_WORKERS=$(nproc)

echo "--- Checking System Dependencies ---"
if ! command -v git &> /dev/null || ! command -v zip &> /dev/null; then
    sudo pacman -S --noconfirm git jdk17-openjdk zip unzip autoconf libtool pkg-config
fi

if ! pip show buildozer &> /dev/null; then
    echo "--- Installing Buildozer ---"
    pip install --user --upgrade git+https://github.com/kivy/buildozer.git@master cython
fi

# 2. FAST CACHE WORKSPACE (Crucial for Speed)
if [ ! -d "$BUILD_WORK_DIR" ]; then
    echo "--- Creating Initial Build Workspace ---"
    mkdir -p "$BUILD_WORK_DIR"
fi

echo "--- Syncing Source Files (Removing Old node_modules) ---"
# EXPLICIT CLEANUP: Ensure no old node_modules or venv exist in the build path
# This fixes the "ValueError: name is too long" error.
rm -rf "$BUILD_WORK_DIR/node_modules"
rm -rf "$BUILD_WORK_DIR/.venv"
rm -rf "$BUILD_WORK_DIR/Belinda_AI"

# Use rsync with --delete to perfectly mirror source, but EXCLUDE the heavy cache folder
rsync -av --delete --progress . "$BUILD_WORK_DIR/" \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude '.git' \
    --exclude 'Belinda_AI' \
    --exclude 'auth_info' \
    --exclude 'build' \
    --exclude 'bin' \
    --exclude 'installer' \
    --exclude 'android_*.log' \
    --exclude 'crash.log' \
    --exclude '.buildozer' # KEEP the cache

cd "$BUILD_WORK_DIR"

echo "--- Starting Ultra-Fast Build (Using $P4A_NUM_WORKERS cores) ---"
# Use 'debug' for fastest packaging
buildozer --allow-root android debug

# 3. Automatic Delivery
PKG_FILE=$(find bin/ -name "*.apk" -mmin -10 | head -n 1)

if [ -f "$PKG_FILE" ]; then
    echo "--- Build successful! ---"
    mkdir -p "$ANDROID_DIST_DIR"
    cp "$PKG_FILE" "$ANDROID_DIST_DIR/Belinda_AI_Manager.apk"
    echo "SUCCESS: APK ready at: $ANDROID_DIST_DIR/Belinda_AI_Manager.apk"
else
    echo "ERROR: Build failed. Check the logs above for specific compile errors."
    exit 1
fi

cd - > /dev/null
