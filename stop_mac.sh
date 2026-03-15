#!/bin/bash

# stop_mac.sh - Stop Belinda_AI on macOS
echo "🛑 Stopping Flask and Bridge processes..."

# Kill python processes running app.py (excluding the installer)
ps aux | grep "python.*app.py" | grep -v "installer" | grep -v "grep" | awk '{print $2}' | xargs kill -9 2>/dev/null || echo "Python bot process not found."

# Kill node processes running bridge.js
pkill -f "node.*bridge.js" || echo "Bridge not running."

echo "✅ All processes stopped."
