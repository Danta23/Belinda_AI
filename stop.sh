#!/bin/bash

echo "🛑 Stopping Flask and Bridge processes..."

# Kill python and node processes related to app.py and bridge.js
# We exclude "installer" to prevent closing the GUI app
pgrep -f "app.py" | grep -v "installer" | xargs -r kill
pgrep -f "bridge.js" | xargs -r kill

echo "✅ All processes stopped."