#!/usr/bin/fish

# stop.fish - Stop Belinda_AI processes using Fish Shell
echo (set_color red)"🛑 Stopping Flask and Bridge processes..."(set_color normal)

# Kill python processes running app.py (excluding the installer)
set pids (ps aux | grep "python.*app.py" | grep -v "installer" | grep -v "grep" | awk '{print $2}')
if test -n "$pids"
    kill -9 $pids
else
    echo "Python bot process not found."
end

# Kill node processes running bridge.js
pkill -f "node.*bridge.js"
or echo "Bridge not running."

echo (set_color green)"✅ All processes stopped."(set_color normal)
