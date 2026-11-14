"""Build the macOS application bundle and disk image (.dmg).

    python scripts/build_macos.py               # create PaperNym.app and package .dmg
    python scripts/build_macos.py --app-only    # create PaperNym.app bundle only
    python scripts/build_macos.py --snapshot    # build snapshot release

Output:
    dist/PaperNym.app
    dist/PaperNym-<version>-macos.dmg
    dist/PaperNym-<version>-macos.dmg.sha256
"""

from __future__ import annotations

import argparse
import hashlib
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_BUNDLE = DIST / "PaperNym.app"


def version() -> str:
    namespace: dict = {}
    exec(
        (ROOT / "src" / "papernym" / "__init__.py").read_text(encoding="utf-8"),
        namespace,
    )
    return namespace["__version__"]


def make_info_plist(ver: str) -> dict:
    return {
        "CFBundleName": "PaperNym",
        "CFBundleDisplayName": "PaperNym",
        "CFBundleIdentifier": "io.github.jubayerprantor.papernym",
        "CFBundleVersion": ver,
        "CFBundleShortVersionString": ver,
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "CFBundleExecutable": "PaperNym",
        "CFBundleIconFile": "papernym",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticGraphicsSwitching": True,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "PDF Document",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": ["com.adobe.pdf"],
            }
        ],
    }


def setup_macos_bundle(bundle_path: Path, ver: str) -> None:
    """Create the macOS .app bundle directory structure."""
    shutil.rmtree(bundle_path, ignore_errors=True)
    contents = bundle_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)

    # Write Info.plist
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(make_info_plist(ver), f)

    # Copy executables from dist/PaperNym if present
    source_dir = DIST / "PaperNym"
    if source_dir.is_dir():
        for item in source_dir.iterdir():
            target = macos / item.name
            if item.is_dir():
                shutil.copytree(item, target, symlinks=True)
            else:
                shutil.copy2(item, target)

    # Icon
    icon_src = ROOT / "src" / "papernym" / "gui" / "icons" / "papernym.png"
    if icon_src.is_file():
        shutil.copy2(icon_src, resources / "papernym.png")


def make_dmg(bundle_path: Path, output_dmg: Path) -> Path:
    """Package the .app bundle into a DMG using hdiutil."""
    hdiutil = shutil.which("hdiutil")
    if not hdiutil:
        raise RuntimeError("hdiutil is required to create DMG packages on macOS")

    temp_dmg = output_dmg.with_name(f"temp_{output_dmg.name}")
    temp_dmg.unlink(missing_ok=True)
    output_dmg.unlink(missing_ok=True)

    cmd = [
        hdiutil,
        "create",
        "-volname",
        "PaperNym",
        "-srcfolder",
        str(bundle_path),
        "-ov",
        "-format",
        "UDZO",
        str(output_dmg),
    ]
    subprocess.run(cmd, check=True)

    sha256 = hashlib.sha256(output_dmg.read_bytes()).hexdigest()
    output_dmg.with_suffix(".dmg.sha256").write_text(
        f"{sha256}  {output_dmg.name}\n", encoding="utf-8"
    )
    print(f"Built {output_dmg} ({output_dmg.stat().st_size // (1024 * 1024)} MB)")
    return output_dmg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-only", action="store_true", help="build .app bundle only")
    parser.add_argument("--snapshot", action="store_true", help="build snapshot release")
    parser.add_argument("--expected-version", help="fail unless version matches this tag")
    args = parser.parse_args()

    ver = version()
    if args.expected_version and args.expected_version.lstrip("v") != ver:
        raise SystemExit(f"version mismatch: expected {args.expected_version}, got {ver}")

    print(f"Creating macOS bundle for PaperNym {ver} at {APP_BUNDLE}...")
    setup_macos_bundle(APP_BUNDLE, ver)

    if args.app_only:
        print(f"macOS bundle created successfully at {APP_BUNDLE}")
        return 0

    if sys.platform != "darwin":
        print("Note: Running hdiutil requires macOS; .app bundle created successfully.")
        return 0

    out_name = f"PaperNym-{ver}-macos.dmg"
    output_path = DIST / out_name
    make_dmg(APP_BUNDLE, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
