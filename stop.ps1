# stop.ps1 - Stop Belinda_AI on Windows 11
Write-Host "🛑 Stopping Flask and Bridge processes..." -ForegroundColor Red

# Stop Python processes running app.py
Get-Process | Where-Object { $_.CommandLine -like "*app.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Node processes running bridge.js
Get-Process | Where-Object { $_.CommandLine -like "*bridge.js*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "✅ All processes stopped." -ForegroundColor Green
