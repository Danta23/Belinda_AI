#!/bin/bash

ENV_FILE=${1:-.env}

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

echo "🚀 Starting Flask server on port $FLASK_PORT..."
python app.py &

sleep 5

echo "🤖 Starting Belinda Bridge on $BRIDGE_HOST:$BRIDGE_PORT (Session: $SESSION_NAME)..."
node bridge.js &
