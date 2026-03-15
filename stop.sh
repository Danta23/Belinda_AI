#!/bin/bash

echo "🛑 Stopping Flask and Bridge processes..."

# Kill python processes related to bot's app.py (excluding this installer)
# We find pids that match app.py but NOT installer
ps aux | grep "python.*app.py" | grep -v "installer" | grep -v "grep" | awk '{print $2}' | xargs -r kill -9

# Kill node process related to bridge.js
pkill -f "node.*bridge.js" || echo "Bridge not running."

echo "✅ All processes stopped."