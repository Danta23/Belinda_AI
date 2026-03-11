#!/data/data/com.termux/files/usr/bin/bash

# start_termux.sh - Start Belinda_AI on Android (Termux)
echo "🚀 Starting Flask server..."
# Termux usually uses 'python' for Python 3
python app.py &

echo "⏳ Waiting for Flask to initialize..."
sleep 5

echo "🔗 Starting WhatsApp Bridge..."
node bridge.js
