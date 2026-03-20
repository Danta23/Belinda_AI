#!/usr/bin/env python3
import sys
import os
import re
import subprocess

def update_version(major=False):
    # Files to update
    main_py = "main.py"
    pkgbuild = "PKGBUILD"
    buildozer_spec = "buildozer.spec"

    # 1. Get current version from main.py (Single Source of Truth)
    if not os.path.exists(main_py):
        print(f"Error: {main_py} not found.")
        return

    with open(main_py, "r") as f:
        main_content = f.read()

    ver_match = re.search(r'APP_VERSION\s*=\s*"([\d.]+)"', main_content)
    if not ver_match:
        # If not found, try to initialize it or get from PKGBUILD as fallback
        print("Warning: APP_VERSION not found in main.py. Trying to initialize...")
        current_ver = "1.0.0" # Default
    else:
        current_ver = ver_match.group(1)

    print(f"Current version found: {current_ver}")

    # Calculate new version
    if major:
        parts = current_ver.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        new_ver = ".".join(parts)
        print(f"Bumping version to {new_ver}...")
    else:
        new_ver = current_ver
        print(f"Maintaining version {new_ver} (Syncing files only)...")

    # 2. Update main.py
    if 'APP_VERSION =' in main_content:
        main_content = re.sub(r'APP_VERSION\s*=\s*"[\d.]+"', f'APP_VERSION = "{new_ver}"', main_content)
    else:
        # Prepend to file
        main_content = f'APP_VERSION = "{new_ver}"\n' + main_content
    
    with open(main_py, "w") as f:
        f.write(main_content)
    print(f"Updated {main_py}")

    # 3. Update PKGBUILD
    if os.path.exists(pkgbuild):
        with open(pkgbuild, "r") as f:
            pkg_content = f.read()
        
        # Get current pkgrel
        rel_match = re.search(r'pkgrel=(\d+)', pkg_content)
        current_rel = int(rel_match.group(1)) if rel_match else 1
        
        new_rel = 1 if major else (current_rel + 1)
        
        pkg_content = re.sub(r'pkgver=[\d.]+', f'pkgver={new_ver}', pkg_content)
        pkg_content = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', pkg_content)
        
        with open(pkgbuild, "w") as f:
            f.write(pkg_content)
        
        # Regenerate .SRCINFO
        print("Regenerating .SRCINFO...")
        try:
            subprocess.run("makepkg --printsrcinfo > .SRCINFO", shell=True, check=True)
        except:
            print("Note: Could not run makepkg (maybe not on Arch/AUR machine?).")
        print(f"Updated {pkgbuild}")

    # 4. Update buildozer.spec
    if os.path.exists(buildozer_spec):
        with open(buildozer_spec, "r") as f:
            spec_content = f.read()
        
        spec_content = re.sub(r'version = [\d.]+', f'version = {new_ver}', spec_content)
        
        with open(buildozer_spec, "w") as f:
            f.write(spec_content)
        print(f"Updated {buildozer_spec}")

    print(f"--- SUCCESS: All version files synchronized to {new_ver} ---")

if __name__ == "__main__":
    is_major = "--major" in sys.argv
    update_version(major=is_major)
