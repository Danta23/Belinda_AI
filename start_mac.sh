#!/bin/bash

# start_mac.sh - Start Belinda_AI on macOS
# Starting Flask server
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python3 app.py &
elif [ -d "venv" ]; then
    source venv/bin/activate
    python3 app.py &
else
    python3 app.py &
fi

echo "⏳ Waiting for Flask to initialize..."
sleep 5

echo "🔗 Starting WhatsApp Bridge..."
node bridge.js
