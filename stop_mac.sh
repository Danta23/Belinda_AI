#!/bin/bash

# stop_mac.sh - Menghentikan bot Belinda AI yang berjalan di tmux

echo "🛑 Menghentikan bot Belinda AI..."

# 1. Cek apakah sesi 'belinda' ada
if tmux has-session -t belinda 2>/dev/null; then
    # Mengirim sinyal Ctrl+C (SIGINT) ke proses di dalam sesi tmux
    tmux send-keys -t belinda C-c
    
    # Tunggu sebentar agar bot menutup koneksi dengan aman
    echo "Menunggu bot menutup koneksi..."
    sleep 5
    
    # 2. Hentikan sesi tmux
    tmux kill-session -t belinda
    echo "✅ Bot Belinda berhasil dihentikan."
else
    echo "⚠️ Sesi 'belinda' tidak ditemukan (bot tidak sedang berjalan)."
fi
