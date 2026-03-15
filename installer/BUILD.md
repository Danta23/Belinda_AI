# 🛠️ Belinda_AI Installer Build Guide

This guide explains how to package the Belinda_AI Setup application for different platforms.

## 🪟 Windows (EXE)
Requires: `PyInstaller`
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Belinda_Setup" --icon "NONE" --add-data "styles.py;." --add-data "settings_manager.py;." installer/app.py
```

## 🐧 Arch Linux (AUR)
1. Copy the `installer/PKGBUILD` to a new directory.
2. Run `makepkg -si`.
3. The application will be installed as `belinda-setup`.

## 🍎 macOS (DMG)
Requires: `py2app`
```bash
pip install py2app
python setup.py py2app
```
(Create a `setup.py` if not already present).

## 📱 Android (APK)
PyQt5 applications can be packaged for Android using **Briefcase (BeeWare)** or **PyQt-Android-Template**.

1. **BeeWare (Recommended)**:
   ```bash
   pip install briefcase
   briefcase create android
   briefcase build android
   briefcase run android
   ```
2. **Kivy/Buildozer**: If performance is an issue, consider porting the UI logic to Kivy, which has native Android support.

---
## 🎨 Design Features
- **Liquid Glass**: Dynamic animated gradients using `FluidGradientWidget`.
- **Glassmorphism**: Semi-transparent panels with drop shadows.
- **Fluent UI**: Responsive layout with smooth transitions.
- **Dark/Light Mode**: Instant theme switching.
