#!/usr/bin/fish

# stop.fish - Stop Belinda_AI processes using Fish Shell
echo (set_color red)"🛑 Stopping Flask and Bridge processes..."(set_color normal)

# Kill python processes running app.py (excluding the installer)
set pids (pgrep -f "app.py" | grep -v "installer")
if test -n "$pids"
    kill $pids
else
    echo "Python bot process not found."
end

# Kill node processes running bridge.js
pkill -f "node bridge.js"
or echo "Node process not found."

echo (set_color green)"✅ All processes stopped."(set_color normal)
