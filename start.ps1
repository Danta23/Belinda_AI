# start.ps1 - Start Belinda_AI on Windows 11
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Action: Detecting Python Environment..." -ForegroundColor Yellow
$PythonPath = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonPath = ".venv\Scripts\python.exe"
    Write-Host "Found .venv environment." -ForegroundColor Green
} elseif (Test-Path "venv\Scripts\python.exe") {
    $PythonPath = "venv\Scripts\python.exe"
    Write-Host "Found venv environment." -ForegroundColor Green
} else {
    Write-Host "Using system python (make sure dependencies are installed)." -ForegroundColor Gray
}

Write-Host "Action: Starting Flask server..." -ForegroundColor Cyan
Start-Process $PythonPath -ArgumentList "app.py" -NoNewWindow

Write-Host "Action: Waiting for Flask to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Action: Starting WhatsApp Bridge..." -ForegroundColor Cyan
node bridge.js
