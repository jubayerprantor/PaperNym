"""Build an AppImage package for Linux.

    python scripts/build_appimage.py               # create AppDir and package .AppImage
    python scripts/build_appimage.py --appdir-only # create AppDir structure only
    python scripts/build_appimage.py --snapshot    # append +git<date>.<sha>

Output:
    dist/PaperNym-<version>-x86_64.AppImage
    dist/PaperNym-<version>-x86_64.AppImage.sha256
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_DIR = DIST / "PaperNym"
APPDIR_ROOT = BUILD / "AppDir"

APPRUN_SCRIPT = """#!/bin/sh
set -e

# Resolve AppDir root
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Detect execution target: CLI or GUI
case "$1" in
  scan|show|watch|wizard|config|keys|status|formats|history|rules|db|test-apis)
    exec "${HERE}/usr/bin/papernym-cli" "$@"
    ;;
  --cli)
    shift
    exec "${HERE}/usr/bin/papernym-cli" "$@"
    ;;
  *)
    TARGET="$(basename "$0")"
    if [ "$TARGET" = "papernym" ] || [ "$TARGET" = "papernym-cli" ]; then
      exec "${HERE}/usr/bin/papernym-cli" "$@"
    else
      exec "${HERE}/usr/bin/PaperNym" "$@"
    fi
    ;;
esac
"""

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=PaperNym
Comment=Academic PDF renamer with scholarly metadata resolution
Exec=PaperNym %F
Icon=papernym
Terminal=false
Categories=Office;Education;Utility;
Keywords=pdf;paper;rename;doi;arxiv;research;
StartupWMClass=PaperNym
MimeType=application/pdf;
"""


def version() -> str:
    namespace: dict = {}
    exec(
        (ROOT / "src" / "papernym" / "__init__.py").read_text(encoding="utf-8"),
        namespace,
    )
    return namespace["__version__"]


def setup_appdir(root: Path, ver: str) -> None:
    """Populate AppDir directory structure for AppImage packaging."""
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    usr_bin = root / "usr" / "bin"
    usr_bin.mkdir(parents=True, exist_ok=True)

    # Copy PyInstaller bundled files if present
    if APP_DIR.is_dir():
        for item in APP_DIR.iterdir():
            dest = usr_bin / item.name
            if item.is_dir():
                shutil.copytree(item, dest, symlinks=True)
            else:
                shutil.copy2(item, dest)

    # AppRun script
    apprun = root / "AppRun"
    apprun.write_text(APPRUN_SCRIPT, encoding="utf-8")
    apprun.chmod(apprun.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Desktop entry
    desktop = root / "papernym.desktop"
    desktop.write_text(DESKTOP_ENTRY, encoding="utf-8")
    apps_dir = root / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(desktop, apps_dir / "papernym.desktop")

    # Icons
    icon_src = ROOT / "src" / "papernym" / "gui" / "icons" / "papernym.png"
    if icon_src.is_file():
        shutil.copy2(icon_src, root / "papernym.png")
        shutil.copy2(icon_src, root / ".DirIcon")

        icon_dir = root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon_src, icon_dir / "papernym.png")

    svg_src = ROOT / "assets" / "papernym-icon.svg"
    if svg_src.is_file():
        svg_dir = root / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        svg_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg_src, svg_dir / "papernym.svg")

    # AppStream Metainfo
    metainfo_src = ROOT / "packaging" / "io.github.jubayerprantor.PaperNym.metainfo.xml"
    if metainfo_src.is_file():
        meta_dir = root / "usr" / "share" / "metainfo"
        meta_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(metainfo_src, meta_dir / metainfo_src.name)


def make_appimage(appdir: Path, output: Path) -> Path:
    """Run appimagetool to produce the AppImage bundle."""
    appimagetool = (
        shutil.which("appimagetool")
        or shutil.which("appimagetool-x86_64.AppImage")
        or "appimagetool"
    )

    env = dict(os.environ, ARCH="x86_64")
    subprocess.run([appimagetool, str(appdir), str(output)], check=True, env=env)

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".AppImage.sha256").write_text(
        f"{sha256}  {output.name}\n", encoding="utf-8"
    )
    print(f"Built {output} ({output.stat().st_size // (1024 * 1024)} MB)")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appdir-only", action="store_true", help="generate AppDir folder only")
    parser.add_argument("--snapshot", action="store_true", help="build snapshot release")
    parser.add_argument("--expected-version", help="fail unless version matches this tag")
    args = parser.parse_args()

    ver = version()
    if args.expected_version and args.expected_version.lstrip("v") != ver:
        raise SystemExit(f"version mismatch: expected {args.expected_version}, got {ver}")

    print(f"Setting up AppDir for PaperNym {ver}...")
    setup_appdir(APPDIR_ROOT, ver)

    if args.appdir_only:
        print(f"AppDir created successfully at {APPDIR_ROOT}")
        return 0

    if sys.platform != "linux":
        print("Note: Running appimagetool requires Linux; AppDir structure created successfully.")
        return 0

    out_name = f"PaperNym-{ver}-x86_64.AppImage"
    output_path = DIST / out_name
    make_appimage(APPDIR_ROOT, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
