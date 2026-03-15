#!/bin/bash

echo "🔄 Resetting Belinda AI environment..."

# Stop running processes
pkill -f "python app.py"
pkill -f "node bridge.js"

# Remove auth session folder (default: auth_info)
if [ -d "auth_info" ]; then
    rm -rf auth_info
    echo "🧹 Removed auth_info session folder."
fi

# Clear chat history
if [ -f "chat_history.json" ]; then
    rm chat_history.json
    echo "🧹 Cleared chat_history.json."
fi

echo "✅ Reset complete. You can now start fresh with ./start.sh"