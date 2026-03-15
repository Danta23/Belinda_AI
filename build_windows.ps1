# Build script for Belinda AI Windows EXE
$OutputDir = "C:\Users\herda\Documents\My Projects\Belinda_AI_App"
if (!(Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir }

Write-Host "Building Windows Executable..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm --onefile --windowed `
    --name "Belinda-AI-Installer" `
    --add-data "installer/styles.py;." `
    --add-data "installer/settings_manager.py;." `
    --add-data "installer/translations.py;." `
    --clean `
    --distpath $OutputDir `
    installer/app.py

Write-Host "Build complete! Check $OutputDir" -ForegroundColor Green
