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

    # Use encoding='utf-8' to avoid UnicodeDecodeError on characters like Japanese text
    with open(main_py, "r", encoding="utf-8") as f:
        main_content = f.read()

    # Match format like 1.0.0 or 1.0.0-1
    ver_match = re.search(r'APP_VERSION\s*=\s*"([\d.-]+)"', main_content)
    if not ver_match:
        print("Error: Could not find APP_VERSION in main.py")
        return

    current_ver_full = ver_match.group(1)
    
    # Split into base version and build counter
    if "-" in current_ver_full:
        base_ver, build_count = current_ver_full.split("-")
        try:
            build_count = int(build_count)
        except ValueError:
            build_count = 1
    else:
        base_ver = current_ver_full
        build_count = 0

    print(f"Current version found: {base_ver} (Build: {build_count})")

    # Calculate new version
    if major:
        parts = base_ver.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        new_base = ".".join(parts)
        new_build = 1
        print(f"Bumping version to {new_base}-1...")
    else:
        new_base = base_ver
        new_build = build_count + 1
        print(f"Syncing with new build counter: {new_build} (v{new_base}-{new_build})...")

    new_ver_str = f"{new_base}-{new_build}"

    # 2. Update main.py
    main_content = re.sub(r'APP_VERSION\s*=\s*"[\d.-]+"', f'APP_VERSION = "{new_ver_str}"', main_content)
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(main_content)
    print(f"Updated {main_py} to v{new_ver_str}")

    # 3. Update PKGBUILD (pkgver=base, pkgrel=build)
    if os.path.exists(pkgbuild):
        with open(pkgbuild, "r", encoding="utf-8") as f:
            pkg_content = f.read()
        
        pkg_content = re.sub(r'pkgver=[\d.]+', f'pkgver={new_base}', pkg_content)
        pkg_content = re.sub(r'pkgrel=\d+', f'pkgrel={new_build}', pkg_content)
        
        with open(pkgbuild, "w", encoding="utf-8") as f:
            f.write(pkg_content)
        
        # Regenerate .SRCINFO
        print("Regenerating .SRCINFO...")
        try:
            subprocess.run("makepkg --printsrcinfo > .SRCINFO", shell=True, check=True)
        except:
            print("Note: Could not run makepkg (maybe not on Arch?).")
        print(f"Updated {pkgbuild}")

    # 4. Update buildozer.spec
    if os.path.exists(buildozer_spec):
        with open(buildozer_spec, "r", encoding="utf-8") as f:
            spec_content = f.read()
        
        # Android compatibility format
        android_ver = f"{new_base}.{new_build}"
        spec_content = re.sub(r'version = [\d.]+', f'version = {android_ver}', spec_content)
        
        with open(buildozer_spec, "w", encoding="utf-8") as f:
            f.write(spec_content)
        print(f"Updated {buildozer_spec} to {android_ver}")

    print(f"--- SUCCESS: All platforms updated to {new_ver_str} ---")

if __name__ == "__main__":
    is_major = "--major" in sys.argv
    update_version(major=is_major)
