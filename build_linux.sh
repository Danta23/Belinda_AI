#!/bin/bash
# Build script for Belinda AI Linux packages (.deb and .rpm)

# --- Configuration ---
APP_NAME="belinda-ai-installer"
ENTRY_POINT="installer/app.py"
# Set the base output directory as requested by the user
# Using WSL path format for better compatibility with Linux tools like fpm
BASE_OUTPUT_DIR="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI_App"
DIST_DIR="$BASE_OUTPUT_DIR"
LINUX_DIST_DIR="$DIST_DIR/linux"
BUILD_DIR="build/linux" # PyInstaller's temporary build directory

# Define the path to the virtual environment
VENV_PATH="/mnt/c/Users/herda/Documents/My Projects/Belinda_AI/.venv"

# Attempt to get version from pyproject.toml, fallback to a default
if [ -f "pyproject.toml" ]; then
    VERSION=$(grep "^version =" pyproject.toml | awk -F'"' '{print $2}')
else
    VERSION="1.4.7" # Fallback
fi

echo "Building version: $VERSION"

# --- Pre-build checks ---
if [[ "$(uname)" != "Linux" ]]; then
    echo "This script is intended to be run on Linux."
    exit 1
fi

# Check if virtual environment is active or python executable exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH. Please create and activate it."
    echo "Expected command: source $VENV_PATH/bin/activate"
    exit 1
fi

PYTHON_EXEC="$VENV_PATH/bin/python"
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "Python executable not found in virtual environment at $PYTHON_EXEC."
    exit 1
fi

# Ensure gem executables are in PATH for fpm to be found
# This path is based on the warning message from gem install and confirmed via gem env
GEM_BIN_PATH="/root/.local/share/gem/ruby/3.4.0/bin"
export PATH="$PATH:$GEM_BIN_PATH"
echo "Ensured gem bin path is in PATH: $GEM_BIN_PATH"
echo "Current PATH: $PATH"

# Check for pyinstaller via virtual environment's python
if ! "$PYTHON_EXEC" -m PyInstaller --version &> /dev/null; then
    echo "PyInstaller not found or not executable within the virtual environment."
    echo "Please ensure it's installed: $VENV_PATH/bin/pip install pyinstaller"
    exit 1
fi

# Check for fpm - now assumes fpm is in PATH after the export
if ! command -v fpm &> /dev/null; then
    echo "fpm (Effing Package Manager) not found, even after PATH update."
    echo "Please ensure Ruby and gem are installed, and then install fpm: sudo gem install fpm"
    echo "For Arch Linux: sudo pacman -S ruby && sudo gem install fpm"
    exit 1
fi

# --- Build Process ---
echo "--- Cleaning up old builds ---"
rm -rf "$BUILD_DIR" "$LINUX_DIST_DIR" "$APP_NAME.spec"
# Ensure the output directory exists
mkdir -p "$LINUX_DIST_DIR"

echo "--- Running PyInstaller using virtual environment's Python ---"
# Combined PyInstaller command into a single line to avoid line continuation issues
"$PYTHON_EXEC" -m PyInstaller --noconfirm --onefile --name "$APP_NAME" --add-data "installer/styles.py:." --add-data "installer/settings_manager.py:." --add-data "installer/translations.py:." --distpath "$LINUX_DIST_DIR" "$ENTRY_POINT"

# Check if PyInstaller was successful
# PyInstaller creates the executable in the DISTPATH when --onefile is used.
# The executable name should match APP_NAME.
if [ ! -f "$LINUX_DIST_DIR/$APP_NAME" ]; then
    echo "PyInstaller failed to create the executable in the distribution path ($LINUX_DIST_DIR). Check the output above for errors."
    exit 1
fi

echo "--- Creating .desktop file and package structure ---"
# FPM needs a directory to package. We'll create a structure like a real filesystem.
PKG_ROOT="$BUILD_DIR/pkg"
rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/usr/local/bin"
mkdir -p "$PKG_ROOT/usr/share/applications"
# Create icon directory if it doesn't exist
mkdir -p "$PKG_ROOT/usr/share/icons/hicolor/128x128/apps"

# Copy the executable from the distpath
cp "$LINUX_DIST_DIR/$APP_NAME" "$PKG_ROOT/usr/local/bin/"

# Create a .desktop file
cat > "$PKG_ROOT/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=Belinda AI Installer
Comment=Setup for Belinda AI WhatsApp Bot
Exec=/usr/local/bin/$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Utility;
EOF

# Copy icon if it exists (using the expected icon name for the desktop file)
if [ -f "icon.png" ]; then
    cp "icon.png" "$PKG_ROOT/usr/share/icons/hicolor/128x128/apps/$APP_NAME.png"
fi

# --- Packaging with FPM ---
echo "--- Creating .deb package ---"
# Combined fpm commands onto single lines to avoid potential parsing issues
fpm -s dir -t deb -n "$APP_NAME" -v "$VERSION" --deb-priority optional --category Utility -p "$LINUX_DIST_DIR" -m "Danta <danta@studio234.id>" --description "Installer for Belinda AI, an intelligent WhatsApp bot." --url "https://github.com/Danta23/Belinda_AI" -C "$PKG_ROOT" usr

echo "--- Creating .rpm package ---"
fpm -s dir -t rpm -n "$APP_NAME" -v "$VERSION" --rpm-summary "Installer for Belinda AI" -p "$LINUX_DIST_DIR" -m "Danta <danta@studio234.id>" --description "Installer for Belinda AI, an intelligent WhatsApp bot." --url "https://github.com/Danta23/Belinda_AI" -C "$PKG_ROOT" usr


echo "--- Cleaning up intermediate files ---"
rm -rf "$BUILD_DIR" "$APP_NAME.spec"

echo "--- Build complete! ---"
echo "Packages available at: $LINUX_DIST_DIR"
