#!/usr/bin/env python3
import sys
import os
import re

def update_version(major=False):
    # Files to update
    main_py = "main.py"
    pkgbuild = "PKGBUILD"
    buildozer_spec = "buildozer.spec"
    pyproject_toml = "pyproject.toml"

    # 1. Get current version from main.py
    if not os.path.exists(main_py):
        print(f"Error: {main_py} not found.")
        return

    with open(main_py, "r", encoding="utf-8") as f:
        main_content = f.read()

    ver_match = re.search(r'APP_VERSION\s*=\s*"([\d.-]+)"', main_content)
    if not ver_match:
        print("Error: Could not find APP_VERSION in main.py")
        return

    current_ver_full = ver_match.group(1)
    
    if "-" in current_ver_full:
        base_ver, build_count = current_ver_full.split("-")
        try: build_count = int(build_count)
        except: build_count = 1
    else:
        base_ver = current_ver_full
        build_count = 0

    # Calculate new version
    if major:
        parts = base_ver.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        new_base = ".".join(parts)
        new_build = 1
    else:
        new_base = base_ver
        new_build = build_count + 1

    new_ver_str = f"{new_base}-{new_build}"
    
    print(f"Bumping version to: {new_ver_str}")

    # 2. Update main.py
    main_content = re.sub(r'APP_VERSION\s*=\s*"[\d.-]+"', f'APP_VERSION = "{new_ver_str}"', main_content)
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(main_content)

    # 3. Update PKGBUILD
    if os.path.exists(pkgbuild):
        with open(pkgbuild, "r", encoding="utf-8") as f:
            pkg_content = f.read()
        pkg_content = re.sub(r'pkgver=[\d.]+', f'pkgver={new_base}', pkg_content)
        pkg_content = re.sub(r'pkgrel=\d+', f'pkgrel={new_build}', pkg_content)
        with open(pkgbuild, "w", encoding="utf-8") as f:
            f.write(pkg_content)

    # 4. Update buildozer.spec
    if os.path.exists(buildozer_spec):
        with open(buildozer_spec, "r", encoding="utf-8") as f:
            spec_content = f.read()
        
        # USE 3-PART VERSION FOR ANDROID
        m_parts = new_base.split(".")
        v_major = m_parts[0]
        v_minor = m_parts[1]
        v_patch = new_build
        safe_android_ver = f"{v_major}.{v_minor}.{v_patch}"
        
        # Calculate a safe 32-bit integer versionCode
        numeric_version = int(v_major)*1000000 + int(v_minor)*1000 + int(v_patch)
        
        # Update string version line
        spec_content = re.sub(r'^version = [\d.]+', f'version = {safe_android_ver}', spec_content, flags=re.MULTILINE)
        
        # Update or add numeric_version
        if re.search(r'^android\.numeric_version = [\d.]+', spec_content, flags=re.MULTILINE):
            spec_content = re.sub(r'^android\.numeric_version = [\d.]+', f'android.numeric_version = {numeric_version}', spec_content, flags=re.MULTILINE)
        else:
            spec_content = re.sub(r'(version = [\d.]+)', f'\\1\nandroid.numeric_version = {numeric_version}', spec_content)

        with open(buildozer_spec, "w", encoding="utf-8") as f:
            f.write(spec_content)
        print(f"Updated {buildozer_spec} to {safe_android_ver} (Numeric: {numeric_version})")

    # 5. Update pyproject.toml
    if os.path.exists(pyproject_toml):
        with open(pyproject_toml, "r", encoding="utf-8") as f:
            toml_content = f.read()
        toml_content = re.sub(r'version\s*=\s*"[\d.-]+"', f'version = "{new_ver_str}"', toml_content, count=1)
        with open(pyproject_toml, "w", encoding="utf-8") as f:
            f.write(toml_content)

    print(f"--- SUCCESS: All platforms synced to {new_ver_str} ---")

if __name__ == "__main__":
    is_major = "--major" in sys.argv
    update_version(major=is_major)
