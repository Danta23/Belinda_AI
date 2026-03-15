#!/usr/bin/fish

# stop.fish - Stop Belinda_AI processes using Fish Shell
echo (set_color red)"🛑 Stopping Flask and Bridge processes..."(set_color normal)

# Kill python processes running app.py
pkill -f "python app.py"
or echo "Python process not found."

# Kill node processes running bridge.js
pkill -f "node bridge.js"
or echo "Node process not found."

echo (set_color green)"✅ All processes stopped."(set_color normal)
