#!/bin/bash
# belinda-ai.sh - Entry point for Arch Linux package (AUR)
# Runs the GUI installer/manager from /opt/belinda-ai

APP_DIR="/opt/belinda-ai"

echo "🚀 Launching Belinda AI..."
exec python "$APP_DIR/installer/app.py"
