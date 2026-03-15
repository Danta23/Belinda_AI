#!/bin/bash
# belinda-ai.sh - Entry point for Arch Linux package

APP_DIR="/opt/belinda-ai"
cd "$APP_DIR"

echo "🚀 Launching Belinda AI Ecosystem..."
python installer/app.py
