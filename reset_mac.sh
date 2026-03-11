#!/bin/bash

# reset_mac.sh - Reset Belinda_AI on macOS
echo "🛑 Stopping Belinda AI..."
pkill -f "python3 app.py"
pkill -f "node bridge.js"

echo "🧹 Resetting WhatsApp auth session..."
rm -rf auth_info
rm -f chat_history.json

echo "✅ All processes stopped & session cleared. Run ./start_mac.sh to login again."
