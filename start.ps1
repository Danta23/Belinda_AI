# start.ps1 - Start Belinda_AI with dependency checks
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Action: Detecting Environment..." -ForegroundColor Yellow
$PythonPath = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonPath = ".venv\Scripts\python.exe"
    Write-Host "Found .venv environment." -ForegroundColor Green
} else {
    Write-Host "WARNING: .venv missing! Use Full Deployment in the installer." -ForegroundColor Red
}

if (!(Test-Path "node_modules")) {
    Write-Host "ERROR: node_modules missing! Please run 'Full Deployment' in the Installer." -ForegroundColor Red
    Pause
    Exit
}

Write-Host "Action: Starting Flask server..." -ForegroundColor Cyan
Start-Process $PythonPath -ArgumentList "app.py" -NoNewWindow

Write-Host "Action: Waiting for Flask to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Action: Starting WhatsApp Bridge..." -ForegroundColor Cyan
node bridge.js
