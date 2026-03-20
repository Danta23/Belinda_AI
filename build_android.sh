#!/bin/bash
# ==============================================================================
# BELINDA AI - REVOLUTIONARY ANDROID BUILD SCRIPT (v3.0 - NUCLEAR CLEAN)
# ==============================================================================
# Feature: Guaranteed versioning, auto-cleanup, and ultra-fast parallel build.
# This version explicitly targets the "Stuck at 1.4.7" bug by wiping stale cache.

# --- CONFIGURATION ---
BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
ANDROID_DIST_DIR="$BASE_OUTPUT_DIR/android"
BUILD_WORK_DIR="/root/belinda_android_build"
VER_FILE="main.py"

# --- 1. DEEP CLEAN PREVIOUS VERSION (NUCLEAR) ---
echo ">>> [1/5] Performing Nuclear Cleanup of Previous Versions..."
# Clean local bin/ remnants
rm -rf bin/
rm -rf .buildozer/android/app
# More aggressive cleaning: remove the entire .buildozer directory to ensure a fresh start
rm -rf .buildozer/
# Clean Windows-side distribution folder (Ensure user always sees the NEWEST one)
if [ -d "$ANDROID_DIST_DIR" ]; then
    echo "    Wiping old APKs from Windows Distribution folder..."
    rm -f "$ANDROID_DIST_DIR"/*.apk
fi

# --- 2. VERSION SYNCHRONIZATION ---
echo ">>> [2/5] Triggering Smart Version Sync..."
# This script updates main.py, buildozer.spec, and pyproject.toml
python3 update_version.py
# Extract version for logging
NEW_VER=$(grep "APP_VERSION =" main.py | cut -d'"' -f2)
echo "    Target Build Version: $NEW_VER"

# --- 3. HARDWARE & MEMORY OPTIMIZATION ---
echo ">>> [3/5] Optimizing Hardware & Memory Resources..."
export P4A_NUM_WORKERS=$(nproc)
# INCREASE GRADLE LIMIT TO 2GB (Since your current RAM is at 84%)
export GRADLE_OPTS="-Xmx2048m -XX:MaxMetaspaceSize=512m -Dorg.gradle.daemon=false"
echo "    Allocating $P4A_NUM_WORKERS CPU cores..."
echo "    Allocating 2048MB to Gradle (No-Daemon mode for stability)..."

# --- 4. WORKSPACE & SYSTEM PREPARATION ---
echo ">>> [4/5] Preparing Mirrored Workspace & Dependencies..."
# Check/Install critical Arch dependencies for P4A/Gradle
echo "    Ensuring Arch Toolchain (zip, unzip, automake, autoconf, libtool, pkg-config)..."
pacman -Sy --noconfirm zip unzip automake autoconf libtool pkg-config patch

# Check for Java 17 (Required for modern Android builds)
if ! command -v java &> /dev/null || ! java -version 2>&1 | grep -q "17"; then
    echo "    Java 17 not found. Correcting environment..."
    pacman -Sy --noconfirm jdk17-openjdk
    archlinux-java set java-17-openjdk
fi

mkdir -p "$BUILD_WORK_DIR"
# Wipe the folder in the build-env to ensure no ghost files exist
rm -rf "$BUILD_WORK_DIR"/*

# Mirror source code to Build Workspace
if ! command -v rsync &> /dev/null; then
    echo "    rsync not found. Installing..."
    pacman -Sy --noconfirm rsync
fi

rsync -av --delete . "$BUILD_WORK_DIR/" \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude '.git' \
    --exclude 'auth_info' \
    --exclude 'build' \
    --exclude 'bin' \
    --exclude '.buildozer' 

cd "$BUILD_WORK_DIR"

# --- 5. THE BUILD (THE FASTEST ALGORITHM) ---
echo ">>> [5/5] Executing Buildozer Optimized Android Pipeline..."
# Pre-build sanity check for versioning string in the spec file
SPEC_VER=$(grep "^version =" buildozer.spec)
echo "    Verifying Buildozer Metadata: $SPEC_VER"

# Execute build with root allowance (Automated 'yes' for root warning)
echo "y" | buildozer --allow-root android debug || {
    echo ">>> [ERROR] Build failed. Inspecting failing build.gradle for diagnostic..."
    GRADLE_FILE="$BUILD_WORK_DIR/.buildozer/android/platform/build-arm64-v8a/dists/belinda_ai_manager/build.gradle"
    if [ -f "$GRADLE_FILE" ]; then
        echo "    --- build.gradle Diagnostic (Lines 20-40) ---"
        sed -n '20,40p' "$GRADLE_FILE" | nl -ba -v20
        echo "    --------------------------------------------"
    else
        echo "    Could not find $GRADLE_FILE for diagnostic."
    fi
    exit 1
}

# --- AUTOMATIC DELIVERY ---
echo "----------------------------------------------------------------"
PKG_FILE=$(find bin/ -name "*.apk" -mmin -5 | head -n 1)

if [ -f "$PKG_FILE" ]; then
    echo ">>> SUCCESS! New version $NEW_VER is ready."
    mkdir -p "$ANDROID_DIST_DIR"
    # Rename with timestamp and version to avoid any caching in user's mind
    TS=$(date +%Y%m%d_%H%M)
    FINAL_NAME="Belinda_AI_${NEW_VER}_${TS}.apk"
    cp "$PKG_FILE" "$ANDROID_DIST_DIR/$FINAL_NAME"
    echo "    APK Path: $ANDROID_DIST_DIR/$FINAL_NAME"
    echo "----------------------------------------------------------------"
    echo "PLEASE UNINSTALL OLD VERSION FROM PHONE BEFORE INSTALLING THIS!"
else
    echo ">>> ERROR: Build failed. See logs above for compilation errors."
    exit 1
fi

cd - > /dev/null
