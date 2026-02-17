Write-Host "🛑 Stopping Belinda AI..."
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "✅ Semua proses Flask & Bridge sudah dihentikan."