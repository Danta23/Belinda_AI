#!/bin/bash
# belinda-ai.sh - Start script for Arch Linux package

APP_DIR="/opt/belinda-ai"
CONF_DIR="$HOME/.config/belinda-ai"

# Create config/storage dir if not exists
mkdir -p "$CONF_DIR/auth_info"

# Check for .env file
if [ ! -f "$CONF_DIR/.env" ]; then
    echo "⚠️  No .env file found in $CONF_DIR"
    echo "Please copy your .env file to $CONF_DIR/.env"
    exit 1
fi

cd "$APP_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Initializing Node.js dependencies..."
    npm install --production
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "🐍 Initializing Python Virtual Environment..."
    python -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Link user config
ln -sf "$CONF_DIR/.env" .env
ln -sf "$CONF_DIR/auth_info" auth_info

echo "🚀 Starting Belinda AI..."
./venv/bin/python app.py & node bridge.js
