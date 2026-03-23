#!/bin/bash
# ==============================================================================
# BELINDA AI - REVOLUTIONARY ANDROID BUILD SCRIPT (v3.0 - NUCLEAR CLEAN)
# ==============================================================================
# Feature: Guaranteed versioning, auto-cleanup, and ultra-fast parallel build.
# This version explicitly targets the "Stuck at 1.4.7" bug by wiping stale cache.

# --- AUTOMATIC VERSION BUMP ---
if [ -f "update_version.py" ]; then
    echo ">>> [AUTO] Incrementing Version..."
    python3 update_version.py
fi

# --- CONFIGURATION ---
# --- CONFIGURATION ---
export PIP_BREAK_SYSTEM_PACKAGES=1
# --- ARGUMENT PARSING ---
DO_CLEAN=false

for arg in "$@"; do
    case $arg in
        -clean)  DO_CLEAN=true ;;
    esac
done

if grep -qi "microsoft" /proc/version || grep -qi "WSL" /proc/version; then
    echo ">>> Detected WSL Environment"
    BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
else
    echo ">>> Detected Native Linux Environment"
    BASE_OUTPUT_DIR="/home/danta/Documents/Projects/Belinda_AI_App"
fi
ANDROID_DIST_DIR="$BASE_OUTPUT_DIR/android"
echo ">>> [CLEAN] Wiping Old Outputs: $ANDROID_DIST_DIR"
rm -rf "$ANDROID_DIST_DIR"
# Use /home partition for build instead of /tmp (tmpfs is too small for modern NDK builds)
BUILD_WORK_DIR="/home/danta/belinda_build_tmp"
VER_FILE="main.py"

# --- 0. SELF-HEALING BUILDOZER (Python 3.14 Compatibility) ---
echo ">>> [0/5] Checking Buildozer Compatibility..."
PROJECT_DIR=$(pwd)
BUILDOZER_VENV="$PROJECT_DIR/.buildozer_venv"
BUILDOZER_BIN="$BUILDOZER_VENV/bin/buildozer"

# Export VIRTUAL_ENV to satisfy Buildozer's venv detection
export VIRTUAL_ENV="$BUILDOZER_VENV"
export PIP_USER=no

# Function to check if buildozer is truly healthy
is_buildozer_healthy() {
    [ -f "$BUILDOZER_BIN" ] || return 1
    "$BUILDOZER_BIN" --version &>/dev/null || return 1
    # Check for critical dependencies in venv
    "$BUILDOZER_VENV/bin/python3" -c "import packaging, pexpect, setuptools" &>/dev/null || return 1
    # Check for FancyURLopener patch
    grep -q "FancyURLopener" $(find "$BUILDOZER_VENV" -name "__init__.py" | grep "buildozer/__init__.py") && return 1
    # Check for distutils patch
    grep -q "distutils.version" $(find "$BUILDOZER_VENV" -name "android.py" | grep "buildozer/targets/android.py") && return 1
    # Check for '--user' patch in android.py
    grep -q "options = \[\"--user\"\]" $(find "$BUILDOZER_VENV" -name "android.py" | grep "buildozer/targets/android.py") && return 1
    return 0
}

if ! is_buildozer_healthy; then
    echo "    ! Buildozer venv is missing, broken, or needs internal patching. Healing..."
    # Re-init only if totally broken
    if ! [ -f "$BUILDOZER_BIN" ] || ! "$BUILDOZER_BIN" --version &>/dev/null; then
        rm -rf "$BUILDOZER_VENV"
        python3 -m venv "$BUILDOZER_VENV"
    fi
    "$BUILDOZER_VENV/bin/pip" install --upgrade pip buildozer pexpect packaging setuptools
    
    # Apply Nuclear Patches (always safe to re-apply)
    PATCH_INIT=$(find "$BUILDOZER_VENV" -name "__init__.py" | grep "buildozer/__init__.py")
    if [ -f "$PATCH_INIT" ]; then
        echo "    ! Applying urlretrieve patch to $PATCH_INIT..."
        sed -i 's/from urllib.request import FancyURLopener/import urllib.request/g' "$PATCH_INIT"
        sed -i '/class ChromeDownloader(FancyURLopener):/,/urlretrieve = ChromeDownloader().retrieve/c\def urlretrieve(url, filename=None, reporthook=None, data=None):\n    opener = urllib.request.build_opener()\n    opener.addheaders = [("User-agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36")]\n    urllib.request.install_opener(opener)\n    return urllib.request.urlretrieve(url, filename, reporthook, data)' "$PATCH_INIT"
    fi
    
    PATCH_ANDROID=$(find "$BUILDOZER_VENV" -name "android.py" | grep "buildozer/targets/android.py")
    if [ -f "$PATCH_ANDROID" ]; then
        echo "    ! Applying distutils and venv patches to $PATCH_ANDROID..."
        # Fix distutils removal in 3.14
        sed -i 's/from distutils.version import LooseVersion/from packaging.version import Version as LooseVersion/g' "$PATCH_ANDROID"
        # Force options = [] to avoid --user error in venv
        sed -i 's/options = \["--user"\]/options = \[\]/g' "$PATCH_ANDROID"
    fi
fi

# ALWAYS prefer the venv
if [ -f "$BUILDOZER_BIN" ]; then
    BUILDOZER_EXE="$BUILDOZER_BIN"
else
    BUILDOZER_EXE="buildozer"
fi
echo "    >>> Using Buildozer Binary: $BUILDOZER_EXE"

# --- 1. CLEANUP (IF REQUESTED) ---
if [ "$DO_CLEAN" = true ]; then
    echo ">>> [CLEAN] Nuclear Cleanup Initiated (-clean flag detected)..."
    rm -rf bin/
    rm -rf .buildozer/
    rm -rf "$BUILD_WORK_DIR"
    echo "    >>> Cleaning Output Directory: $BASE_OUTPUT_DIR"
    rm -f "$BASE_OUTPUT_DIR"/*.apk
    rm -f "$ANDROID_DIST_DIR"/*.apk
    echo "    Cache and old binaries wiped. Starting fresh."
fi

# --- 2. DEEP VERIFICATION ---
echo ">>> [1/5] Verifying Resources & Environment..."
# Check for available disk space in the build partition (need at least 8GB)
AVAIL_SPACE=$(df -h "$HOME" | awk 'NR==2 {print $4}' | sed 's/G//')
if (( $(echo "$AVAIL_SPACE < 8" | bc -l) )); then
    echo "    [WARNING] Low Disk Space: Only ${AVAIL_SPACE}GB available. Android builds may fail."
fi

# Check/Install critical Arch dependencies
echo "    Ensuring Arch Toolchain (zip, unzip, automake, autoconf, libtool, pkg-config, cython, ant, wget)..."
sudo pacman -Sy --noconfirm zip unzip automake autoconf libtool pkg-config patch cython ant wget \
    python-appdirs python-colorama python-jinja python-sh python-build python-toml python-packaging python-setuptools

# Pre-fetch Android SDK Command Line Tools (Nuclear Path Fix)
SDK_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-6514223_latest.zip"
SDK_TOOLS_DIR="$HOME/.buildozer/android/platform/android-sdk"
SDK_ZIP="$SDK_TOOLS_DIR/commandlinetools-linux-6514223_latest.zip"
mkdir -p "$SDK_TOOLS_DIR"

if [ ! -f "$SDK_TOOLS_DIR/tools/bin/sdkmanager" ]; then
    echo "    ! SDK Manager missing. Preparing Nuclear SDK Fix..."
    if [ ! -f "$SDK_ZIP" ] || ! unzip -tq "$SDK_ZIP" &>/dev/null; then
        echo "    ! SDK Zip missing or corrupted. Fetching..."
        rm -f "$SDK_ZIP"
        wget -c --show-progress "$SDK_TOOLS_URL" -P "$SDK_TOOLS_DIR"
    fi
    echo "    ! Manually unpacking SDK Tools..."
    unzip -q "$SDK_ZIP" -d "$SDK_TOOLS_DIR"
    if [ ! -f "$SDK_TOOLS_DIR/tools/bin/sdkmanager" ]; then
        echo "    ! ERROR: SDK Manager still not found after extract."
        exit 1
    fi
else
    echo "    >>> SDK Manager is ready."
fi

# Pre-fetch Android NDK (Nuclear Integrity & Manual Extract)
NDK_URL="https://dl.google.com/android/repository/android-ndk-r25b-linux.zip"
NDK_DIR="$HOME/.buildozer/android/platform"
NDK_ZIP="$NDK_DIR/android-ndk-r25b-linux.zip"
NDK_EXTRACTED_DIR="$NDK_DIR/android-ndk-r25b"
mkdir -p "$NDK_DIR"

check_ndk_ready() {
    if [ -d "$NDK_EXTRACTED_DIR" ] && [ -f "$NDK_EXTRACTED_DIR/ndk-build" ]; then
        return 0
    fi
    return 1
}

if ! check_ndk_ready; then
    echo "    ! NDK missing or incomplete. Preparing Nuclear Download/Extract..."
    if [ ! -f "$NDK_ZIP" ] || ! unzip -tq "$NDK_ZIP" &>/dev/null; then
        echo "    ! Zip missing or corrupted. Fetching r25b..."
        rm -f "$NDK_ZIP"
        wget -c --show-progress "$NDK_URL" -P "$NDK_DIR"
    fi
    echo "    ! Manually unpacking NDK to avoid Buildozer unzip bugs..."
    rm -rf "$NDK_EXTRACTED_DIR"
    unzip -q "$NDK_ZIP" -d "$NDK_DIR" || { echo "    ! ERROR: Unzip failed. Disk full?"; exit 1; }
    if ! check_ndk_ready; then
        echo "    ! ERROR: NDK still not ready after extract."
        exit 1
    fi
else
    echo "    >>> NDK is ready and verified."
fi

# Check for Java 17 (Required for modern Android builds)
if ! command -v java &> /dev/null || ! java -version 2>&1 | grep -q "17"; then
    echo "    Java 17 not found. Correcting environment..."
    sudo pacman -Sy --noconfirm jdk17-openjdk
    sudo archlinux-java set java-17-openjdk
fi

mkdir -p "$BUILD_WORK_DIR"
# Wipe the folder in the build-env to ensure no ghost files exist
rm -rf "$BUILD_WORK_DIR"/*

# Mirror source code to Build Workspace
if ! command -v rsync &> /dev/null; then
    echo "    rsync not found. Installing..."
    sudo pacman -Sy --noconfirm rsync
fi

rsync -av --delete . "$BUILD_WORK_DIR/" \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude '.git' \
    --exclude 'auth_info' \
    --exclude 'build_android' \
    --exclude 'build' \
    --exclude 'bin' \
    --exclude '.buildozer' 

cd "$BUILD_WORK_DIR"

# --- Check Disk Space ---
FREE_SPACE_KB=$(df -k / | tail -n 1 | awk '{print $4}')
if [ "$FREE_SPACE_KB" -lt 1000000 ]; then
    echo "    ! WARNING: Very low disk space ($((FREE_SPACE_KB/1024)) MB). The build may fail."
    echo "    ! Cleaning caches again..."
    rm -rf ~/.cache/*
fi

# --- 5. THE BUILD (THE FASTEST ALGORITHM) ---
echo ">>> [5/5] Executing Buildozer Optimized Android Pipeline..."

# PRE-CLONE & PATCH P4A (Nuclear Option for Python 3.14 stability)
echo "    Preparing Toolchain (p4a Intercept)..."
cd "$BUILD_WORK_DIR"
# Direct clone if missing (more reliable than buildozer help)
P4A_DIR="$BUILD_WORK_DIR/.buildozer/android/platform/python-for-android"
if [ ! -d "$P4A_DIR" ]; then
    echo "    >>> Cloning python-for-android (develop)..."
    mkdir -p "$(dirname "$P4A_DIR")"
    git clone -b develop --single-branch https://github.com/kivy/python-for-android.git "$P4A_DIR"
fi
P4A_RECIPE_PY=$(find "$BUILD_WORK_DIR/.buildozer" -name "recipe.py" | grep "pythonforandroid/recipe.py" | head -n 1)
if [ -f "$P4A_RECIPE_PY" ]; then
    echo "    ! Patching Toolchain Downloader: $P4A_RECIPE_PY"
    # Nuclear Fix for IncompleteRead: Replace urllib with wget for recipe downloads
    # 1. Ensure imports
    sed -i '1iimport subprocess' "$P4A_RECIPE_PY"
    # 2. Replace the entire http/https download block with wget
    # We target the specific lines found in p4a recipe.py
    sed -i '/if parsed_url.scheme in (.http., .https.):/,/return target/c\        if parsed_url.scheme in ("http", "https"):\n            print(f"    >>> Nuclear Download (wget): {url}")\n            if exists(target): unlink(target)\n            subprocess.run(["wget", "-c", "--show-progress", "--no-check-certificate", url, "-O", target], check=True)\n            return target' "$P4A_RECIPE_PY"
fi

# --- 5. THE BUILD (THE FASTEST ALGORITHM) ---
while true; do
    echo ">>> [5/5] Executing Buildozer Optimized Android Pipeline..."
    # Pre-build sanity check for versioning string in the spec file
    SPEC_VER=$(grep "^version =" buildozer.spec)
    echo "    Verifying Buildozer Metadata: $SPEC_VER"

    # Define project-local log file for easier access (absolute path)
    LOG_FILE="$PROJECT_DIR/build_error.log"
    rm -f "$LOG_FILE"

    # Execute build with root allowance and capture logs
    echo ">>> Executing Buildozer (Logs are being saved to $LOG_FILE)"
    yes "y" | $BUILDOZER_EXE --allow-root android debug 2>&1 | tee "$LOG_FILE"
    
    # Check exit status of buildozer (PIPESTATUS[1] is Buildozer, PIPESTATUS[0] is 'yes')
    BUILDOZER_STATUS=${PIPESTATUS[1]}
    
    # [SAFETY CHECK] Even if buildozer returns non-zero, check if an APK was actually made
    LATEST_APK=$(find bin/ -name "*.apk" -mmin -2 | head -n 1)
    
    if [ $BUILDOZER_STATUS -eq 0 ] || [ -f "$LATEST_APK" ]; then
        echo ">>> Build successfully completed."
        if [ $BUILDOZER_STATUS -ne 0 ]; then
            echo "    (Note: Buildozer returned code $BUILDOZER_STATUS but APK was successfully produced.)"
        fi
        rm -f "$LOG_FILE"  # Clean up log on success
        break
    else
        echo "----------------------------------------------------------------"
        echo ">>> [!] BUILD FAILED (Status: $BUILDOZER_STATUS). Log saved to: $LOG_FILE"
        
        # --- AUTO-REPAIR LOGIC ---
        # 1. Check for FancyURLopener Error (Python 3.14 compatibility)
        if grep -q "ImportError: cannot import name 'FancyURLopener'" "$LOG_FILE"; then
            echo ">>> DETECTED: Buildozer Compatibility Error (Python 3.14+)"
            read -p ">>> Would you like to AUTO-PATCH Buildozer now? (Requires sudo) (y/n): " fix_confirm
            if [[ "$fix_confirm" =~ ^[Yy]$ ]]; then
                # Find the actual buildozer __init__.py file
                B_FILE=$(python3 -c "import buildozer; print(buildozer.__file__)" 2>/dev/null)
                if [ -f "$B_FILE" ]; then
                    echo "    >>> Patching $B_FILE..."
                    # Replace the import and the class inheritance/usage globally
                    sudo sed -i "s/from urllib.request import FancyURLopener/import urllib.request/g" "$B_FILE"
                    sudo sed -i "s/FancyURLopener/object/g" "$B_FILE"
                    echo ">>> Patch applied successfully. Retrying build..."
                    continue
                else
                    echo "    [ERROR] Could not locate buildozer source for patching."
                fi
            fi
        fi

        # 2. Check for Disk Quota
        if grep -q "Disk quota exceeded" "$LOG_FILE"; then
            echo ">>> DETECTED: Storage Constraint (Disk quota exceeded)"
            read -p ">>> Would you like to clear the .buildozer cache? (y/n): " fix_confirm
            if [[ "$fix_confirm" =~ ^[Yy]$ ]]; then
                rm -rf ~/.buildozer/android/platform/* 
                echo ">>> Cache cleared. Retrying..."
                continue
            fi
        fi

        # 3. Interactive Prompt
        echo ""
        read -p ">>> Options: (v)iew log, (r)etry, (e)xit: " opt
        case $opt in
            v|V)
                if command -v less &>/dev/null; then less "$LOG_FILE"; else cat "$LOG_FILE"; fi
                ;;
            r|R)
                echo ">>> Restarting build process..."
                cd - > /dev/null
                continue
                ;;
            *)
                echo ">>> Build aborted."
                cd - > /dev/null
                exit 1
                ;;
        esac
    fi
done

# --- AUTOMATIC DELIVERY ---
echo "----------------------------------------------------------------"
echo ">>> [6/6] Delivering APK to Output Directory..."

# Re-verify latest version from main.py
NEW_VER=$(grep "APP_VERSION =" "$PROJECT_DIR/main.py" | cut -d'"' -f2)

# Find the APK - look in bin/ first, then deep search if needed
PKG_FILE=$(find bin/ -name "*.apk" -mmin -10 | head -n 1)
if [ -z "$PKG_FILE" ]; then
    echo "    ! APK not found in bin/. Searching build outputs..."
    PKG_FILE=$(find .buildozer/android/platform/build-arm64-v8a/dists -name "*.apk" -mmin -10 | head -n 1)
fi

if [ -f "$PKG_FILE" ]; then
    mkdir -p "$BASE_OUTPUT_DIR"
    mkdir -p "$ANDROID_DIST_DIR"
    
    TS=$(date +%Y%m%d_%H%M)
    FINAL_NAME="Belinda_AI_${NEW_VER}_${TS}.apk"
    
    echo "    >>> Copying APK to: $BASE_OUTPUT_DIR"
    cp -v "$PKG_FILE" "$BASE_OUTPUT_DIR/$FINAL_NAME"
    cp -v "$PKG_FILE" "$ANDROID_DIST_DIR/$FINAL_NAME"
    
    echo "----------------------------------------------------------------"
    echo ">>> SUCCESS! New version $NEW_VER is ready."
    echo "    Output Path: $BASE_OUTPUT_DIR/$FINAL_NAME"
    echo "----------------------------------------------------------------"
else
    echo ">>> ERROR: Build claimed success but no APK was found in worker directory."
    echo "    Check: $BUILD_WORK_DIR/bin/"
    exit 1
fi

cd - > /dev/null
