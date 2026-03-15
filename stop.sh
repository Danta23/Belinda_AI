#!/bin/bash

echo "🛑 Stopping Flask and Bridge processes..."

# Kill python and node processes related to app.py and bridge.js
pkill -f "app.py"
pkill -f "bridge.js"

echo "✅ All processes stopped."