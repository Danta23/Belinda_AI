# start.ps1 - Start Belinda_AI on Windows 11
Write-Host "🚀 Starting Flask server..." -ForegroundColor Cyan
if (Test-Path "venv\Scripts\python.exe") {
    Start-Process "venv\Scripts\python.exe" -ArgumentList "app.py" -NoNewWindow
} else {
    Start-Process "python" -ArgumentList "app.py" -NoNewWindow
}

Write-Host "⏳ Waiting for Flask to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "🔗 Starting WhatsApp Bridge..." -ForegroundColor Cyan
node bridge.js
