#!/bin/bash

ENV_FILE=${1:-.env}

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Starting Flask server
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python app.py &
else
    python app.py &
fi

sleep 5

echo "🤖 Starting Belinda Bridge on $BRIDGE_HOST:$BRIDGE_PORT (Session: $SESSION_NAME)..."
node bridge.js &
