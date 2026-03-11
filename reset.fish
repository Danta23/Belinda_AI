#!/usr/bin/fish

# reset.fish - Reset Belinda_AI session using Fish Shell
echo (set_color red)"🛑 Stopping Belinda AI..."(set_color normal)
pkill -f "python app.py"
pkill -f "node bridge.js"

echo (set_color yellow)"🧹 Resetting WhatsApp auth session..."(set_color normal)
rm -rf auth_info
rm -f chat_history.json

echo (set_color green)"✅ All processes stopped & session cleared. Run ./start.fish to login again."(set_color normal)
