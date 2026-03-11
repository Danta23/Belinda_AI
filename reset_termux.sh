#!/data/data/com.termux/files/usr/bin/bash

# reset_termux.sh - Reset Belinda_AI on Android (Termux)
echo "🛑 Stopping Belinda AI..."
pkill -f "python app.py"
pkill -f "node bridge.js"

echo "🧹 Resetting WhatsApp auth session..."
rm -rf auth_info
rm -f chat_history.json

echo "✅ All processes stopped & session cleared. Run ./start_termux.sh to login again."
