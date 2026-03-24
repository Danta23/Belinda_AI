#!/bin/bash
# ==============================================================================
# BELINDA AI - BEEWARE ANDROID BUILD SCRIPT (v4.1)
# ==============================================================================
set -e

# --- OUTPUT DIRECTORY CONFIGURATION ---
BASE_OUTPUT_DIR="/home/danta/Documents/Projects/Belinda_AI_App"
echo "====================================================================="
echo ">>> [1/5] CLEANING UP OLD FILES & PREPARING OUTPUT DIRECTORY..."
echo "====================================================================="
rm -rf .buildozer/
rm -rf bin/
rm -f buildozer.spec
rm -rf /home/danta/belinda_build_tmp

# Hapus APK sebelumnya agar tidak konflik
echo ">>> Cleaning old APKs in $BASE_OUTPUT_DIR..."
mkdir -p "$BASE_OUTPUT_DIR"
rm -f "$BASE_OUTPUT_DIR"/*.apk

echo "====================================================================="
echo ">>> [2/5] PREPARING PYTHON ENVIRONMENT..."
echo "====================================================================="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
if [[ "$SHELL" == *"fish"* ]]; then
    source .venv/bin/activate.fish || true
else
    source .venv/bin/activate || true
fi
pip install --upgrade pip setuptools wheel
pip install briefcase toga python-dotenv

echo "====================================================================="
echo ">>> [3/5] STRUCTURING PROJECT FOR BEEWARE..."
echo "====================================================================="
mkdir -p src/belinda_ai
cp main.py src/belinda_ai/app.py
touch src/belinda_ai/__init__.py
cat << 'EOF' > src/belinda_ai/__main__.py
from belinda_ai.app import main

if __name__ == '__main__':
    main().main_loop()
EOF

if [ -f "pyproject.toml" ]; then
    sed -i 's/app_module = "belinda_ai.android_app"/app_module = "belinda_ai.app"/g' pyproject.toml
fi

echo "====================================================================="
echo ">>> [4/5] COMPILING APK USING BRIEFCASE..."
echo "====================================================================="
export BRIEFCASE_NO_PROMPT=1
export BRIEFCASE_DEV=1

echo ">>> Creating Android Project Template..."
briefcase create android

echo ">>> Building Gradle App..."
briefcase build android

echo ">>> Packaging APK..."
briefcase package android

echo "====================================================================="
echo ">>> [5/5] DELIVERING APK..."
echo "====================================================================="
# E.g., build/belinda-ai/android/gradle/app/build/outputs/apk/debug/app-debug.apk
APK_PATH=$(find build/ -name "*.apk" | grep -i "debug" | head -n 1)

if [ -f "$APK_PATH" ]; then
    FINAL_NAME="Belinda_AI_BeeWare_Latest.apk"
    cp -v "$APK_PATH" "$BASE_OUTPUT_DIR/$FINAL_NAME"
    
    echo "----------------------------------------------------------------"
    echo ">>> SUCCESS! Compilation Completed."
    echo ">>> Your Android App is ready at: $BASE_OUTPUT_DIR/$FINAL_NAME"
    echo "----------------------------------------------------------------"
else
    echo ">>> ERROR: Compilation failed. No APK was generated."
    exit 1
fi
