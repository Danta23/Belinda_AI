#!/usr/bin/fish

# start.fish - Start Belinda_AI using Fish Shell
set -x PYTHON_URL "http://127.0.0.1:8000"

echo (set_color cyan)"🚀 Starting Flask server..."(set_color normal)
if test -d ".venv"
    source .venv/bin/activate.fish
    python app.py &
else if test -d "venv"
    source venv/bin/activate.fish
    python app.py &
else
    python app.py &
end

echo (set_color yellow)"⏳ Waiting for Flask to initialize..."(set_color normal)
sleep 5

echo (set_color cyan)"🔗 Starting WhatsApp Bridge..."(set_color normal)
node bridge.js
