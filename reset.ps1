Write-Host "🛑 Stopping Belinda AI..."
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "🧹 Resetting WhatsApp auth session..."
Remove-Item -Recurse -Force auth_info

Write-Host "✅ Semua proses dihentikan & auth session dihapus. Jalankan start.ps1 untuk login ulang."