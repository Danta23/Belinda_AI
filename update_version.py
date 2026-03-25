#!/usr/bin/env python3
import sys
import os
import re

def update_version(major=False):
    # Files to update
    main_py = "main.py"
    pkgbuild = "PKGBUILD"
    buildozer_spec = "buildozer.spec" # Not currently used, but keep for future
    pyproject_toml = "pyproject.toml"

    # 1. Get current version from main.py
    if not os.path.exists(main_py):
        print(f"Error: {main_py} not found.")
        return

    with open(main_py, "r", encoding="utf-8") as f:
        main_content = f.read()

    ver_match = re.search(r'APP_VERSION\s*=\s*"(.+?)"', main_content)
    if not ver_match:
        print("Error: Could not find APP_VERSION in main.py")
        return

    current_ver_full = ver_match.group(1)
    
    # Try to parse new format: X.Y.Z.W-archN-B (e.g., 1.4.7.2-arch1-1)
    match = re.match(r'(?P<base_ver>[\d.]+)-(?P<arch_part>arch\d+)-(?P<build_count>\d+)', current_ver_full)
    if match:
        base_ver = match.group('base_ver')
        arch_part = match.group('arch_part')
        build_count = int(match.group('build_count'))
    else:
        # Fallback to old formats if new format not matched
        print(f"Warning: '{current_ver_full}' not in expected format (X.Y.Z.W-archN-B). Trying simpler parse.")
        if "-" in current_ver_full:
            parts = current_ver_full.split("-")
            base_ver = "-".join(parts[:-1]) # Base could be 1.4.7.2-Arch (previous state)
            try:
                build_count = int(parts[-1])
                arch_part = "arch1" # Default if not explicitly found
            except ValueError:
                base_ver = current_ver_full
                build_count = 0
                arch_part = "arch1"
        else:
            base_ver = current_ver_full
            build_count = 0
            arch_part = "arch1" # Default arch part

    # Calculate new version parts
    if major:
        parts = base_ver.split(".")
        # Increment the last segment of the base version
        parts[-1] = str(int(parts[-1]) + 1)
        new_base = ".".join(parts)
        new_build_count = 1
        new_arch_part = "arch1"
    else:
        new_base = base_ver
        new_build_count = build_count + 1
        new_arch_part = arch_part # Keep existing arch part

    # Construct the display version for main.py (e.g., 1.4.7.2-arch1-2)
    new_ver_str_for_main_py = f"{new_base}-{new_arch_part}-{new_build_count}"
    
    # Construct the PEP440 compliant version for build systems (e.g., 1.4.7.2.post2)
    final_ver_for_build_systems = f"{new_base}.post{new_build_count}"

    print(f"Bumping version to: {new_ver_str_for_main_py} (for main.py) and {final_ver_for_build_systems} (for build systems)")

    # 2. Update main.py
    main_content = re.sub(r'APP_VERSION\s*=\s*".+?"', f'APP_VERSION = "{new_ver_str_for_main_py}"', main_content)
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(main_content)

    # 3. Update PKGBUILD
    if os.path.exists(pkgbuild):
        with open(pkgbuild, "r", encoding="utf-8") as f:
            pkg_content = f.read()
        pkg_content = re.sub(r'pkgver=[\d.]+', f'pkgver={new_base}', pkg_content)
        pkg_content = re.sub(r'pkgrel=\d+', f'pkgrel={new_build_count}', pkg_content)
        with open(pkgbuild, "w", encoding="utf-8") as f:
            f.write(pkg_content)

    # 4. Update pyproject.toml with PEP440 version
    if os.path.exists(pyproject_toml):
        with open(pyproject_toml, "r", encoding="utf-8") as f:
            toml_content = f.read()
        toml_content = re.sub(r'version\s*=\s*".+?"', f'version = "{final_ver_for_build_systems}"', toml_content, count=1)
        with open(pyproject_toml, "w", encoding="utf-8") as f:
            f.write(toml_content)

    print(f"--- SUCCESS: All platforms synced. Display: {new_ver_str_for_main_py} | Build: {final_ver_for_build_systems} ---")

if __name__ == "__main__":
    is_major = "--major" in sys.argv
    update_version(major=is_major)
