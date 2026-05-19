#!/bin/bash

# start_mac.sh - Start Belinda_AI on macOS with tmux
# Ensure no system-level GROQ_API_KEY overrides our .env
unset GROQ_API_KEY

# Cek apakah sesi 'belinda' sudah ada
if tmux has-session -t belinda 2>/dev/null; then
    echo "Sesi 'belinda' sudah berjalan. Langsung masuk..."
    tmux attach-session -t belinda
else
    echo "Memulai sesi baru 'belinda'..."
    # Menjalankan bot di background session dan tetap hidup dengan exec bash
    tmux new-session -d -s belinda 'bash start.sh; exec bash'
    echo "Bot sudah berjalan di background (tmux). Otomatis masuk..."
    tmux attach-session -t belinda
fi
