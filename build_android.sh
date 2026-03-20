#!/bin/bash
# ULTRA-FAST Build Script for Belinda AI Manager (v2 - Fixed Path Length Error)
# Always builds from latest main.py and synchronizes version.

BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
ANDROID_DIST_DIR="$BASE_OUTPUT_DIR/android"
BUILD_WORK_DIR="/root/belinda_android_build"

# 1. Update Tools and APP VERSION
echo "--- Updating APP Version ---"
# This will update version in main.py, PKGBUILD, and buildozer.spec
python3 update_version.py

# 2. Multi-Core Acceleration (Use all available CPU cores)
export P4A_NUM_WORKERS=$(nproc)

echo "--- Checking System Dependencies ---"
if ! command -v git &> /dev/null || ! command -v zip &> /dev/null; then
    sudo pacman -S --noconfirm git jdk17-openjdk zip unzip autoconf libtool pkg-config
fi

# Always Upgrade Buildozer and Pip to latest
echo "--- Updating Pip and Buildozer ---"
pip install --user --upgrade pip buildozer cython

# 2. FAST CACHE WORKSPACE (Crucial for Speed)
if [ ! -d "$BUILD_WORK_DIR" ]; then
    echo "--- Creating Initial Build Workspace ---"
    mkdir -p "$BUILD_WORK_DIR"
fi

echo "--- Syncing LATEST Source Files (Mirroring main.py) ---"
# EXPLICIT CLEANUP: Ensure no old node_modules or venv exist in the build path
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
