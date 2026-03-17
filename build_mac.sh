#!/bin/bash
# Build script for Belinda AI macOS DMG

# --- Configuration ---
APP_NAME="Belinda-AI-Installer"
ENTRY_POINT="installer/app.py"
# Set the base output directory as requested by the user
BASE_OUTPUT_DIR="C:/Users/herda/Documents/My Projects/Belinda_AI_App"
DIST_DIR="$BASE_OUTPUT_DIR"
MAC_DIST_DIR="$DIST_DIR/macos"
FINAL_DMG_NAME="Belinda-AI-Installer.dmg"

# --- Pre-build checks ---
# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "This script is intended to be run on macOS."
    exit 1
fi

# Check for pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Please install it with: pip install pyinstaller"
    exit 1
fi

# Check for hdiutil
if ! command -v hdiutil &> /dev/null; then
    echo "hdiutil not found. This script requires macOS command line tools."
    exit 1
fi

# --- Build Process ---
echo "--- Cleaning up old builds ---"
rm -rf build "$MAC_DIST_DIR" "$APP_NAME.spec"
# Ensure the output directory exists
mkdir -p "$MAC_DIST_DIR"

echo "--- Running PyInstaller to create .app bundle ---"
pyinstaller --noconfirm --windowed 
    --name "$APP_NAME" 
    --add-data "installer/styles.py:." 
    --add-data "installer/settings_manager.py:." 
    --add-data "installer/translations.py:." 
    --distpath "$MAC_DIST_DIR" 
    "$ENTRY_POINT"

# Check if PyInstaller was successful
if [ ! -d "$MAC_DIST_DIR/$APP_NAME.app" ]; then
    echo "PyInstaller failed to create the .app bundle. Check the output above for errors."
    exit 1
fi

echo "--- Creating .dmg disk image ---"
hdiutil create -volname "$APP_NAME" 
    -srcfolder "$MAC_DIST_DIR/$APP_NAME.app" 
    -ov -format UDZO 
    "$MAC_DIST_DIR/$FINAL_DMG_NAME"

echo "--- Cleaning up intermediate files ---"
rm -rf build "$APP_NAME.spec"
rm -rf "$MAC_DIST_DIR/$APP_NAME.app" # remove the .app bundle as it is now in the dmg

echo "--- Build complete! ---"
echo "DMG available at: $MAC_DIST_DIR/$FINAL_DMG_NAME"

