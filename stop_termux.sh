#!/data/data/com.termux/files/usr/bin/bash

# stop_termux.sh - Stop Belinda_AI on Android (Termux)
echo "🛑 Stopping Flask and Bridge processes..."

pkill -f "python app.py" || echo "Python process not found."
pkill -f "node bridge.js" || echo "Node process not found."

echo "✅ All processes stopped."
