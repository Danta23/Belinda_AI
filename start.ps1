# Load environment variables dari .env
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^(.*?)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [System.Environment]::SetEnvironmentVariable($name, $value)
        }
    }
}

Write-Host "🚀 Starting Flask server..."
Start-Process powershell -ArgumentList "python app.py" -NoNewWindow

Start-Sleep -Seconds 5

Write-Host "🤖 Starting Belinda Bridge on $env:BRIDGE_HOST:$env:BRIDGE_PORT (Session: $env:SESSION_NAME)..."
Start-Process powershell -ArgumentList "node bridge.js" -NoNewWindow