#!/bin/bash

# stop_mac.sh - Stop Belinda_AI on macOS
echo "🛑 Stopping Flask and Bridge processes..."

# Kill python processes running app.py
pkill -f "python3 app.py" || echo "Python process not found."

# Kill node processes running bridge.js
pkill -f "node bridge.js" || echo "Node process not found."

echo "✅ All processes stopped."
