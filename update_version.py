#!/usr/bin/env python3
import sys
import os
import re
import subprocess

def update_version(major=False):
    pkgbuild_path = "PKGBUILD"
    if not os.path.exists(pkgbuild_path):
        print("Error: PKGBUILD not found.")
        return

    with open(pkgbuild_path, "r") as f:
        content = f.read()

    # Get current version
    ver_match = re.search(r'pkgver=([\d.]+)', content)
    rel_match = re.search(r'pkgrel=(\d+)', content)

    if not ver_match or not rel_match:
        print("Error: Could not parse pkgver or pkgrel.")
        return

    current_ver = ver_match.group(1)
    current_rel = int(rel_match.group(1))

    if major:
        # Increment last digit of version
        parts = current_ver.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        new_ver = ".".join(parts)
        new_rel = 1
        content = re.sub(r'pkgver=[\d.]+', f'pkgver={new_ver}', content)
        content = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', content)
        print(f"Bumping version to {new_ver}-1")
    else:
        # Just increment pkgrel
        new_rel = current_rel + 1
        content = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', content)
        print(f"Bumping pkgrel to {new_rel}")

    with open(pkgbuild_path, "w") as f:
        f.write(content)

    # Regenerate .SRCINFO
    print("Regenerating .SRCINFO...")
    subprocess.run("makepkg --printsrcinfo > .SRCINFO", shell=True, check=True)

    # Push to AUR if in correct branch
    print("Updates applied locally. To push to AUR, use:")
    print("git add PKGBUILD .SRCINFO && git commit -m 'chore: bump version' && git push origin master")

if __name__ == "__main__":
    is_major = "--major" in sys.argv
    update_version(major=is_major)
