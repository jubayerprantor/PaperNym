"""Install or remove Windows File Explorer context menu integration for PaperNym.

Adds right-click options to Windows File Explorer (Current User only, no admin needed):
- On .pdf files: "Rename with PaperNym", "Inspect with PaperNym"
- On folders: "Rename PDFs with PaperNym"

Usage:
    python scripts/install_context_menu.py --install
    python scripts/install_context_menu.py --uninstall
    python scripts/install_context_menu.py --status
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Registry keys to register under HKCU
PDF_KEY_BASE = r"Software\Classes\SystemFileAssociations\.pdf\shell"
DIR_KEY_BASE = r"Software\Classes\Directory\shell"
DIR_BG_KEY_BASE = r"Software\Classes\Directory\Background\shell"


def find_executables() -> tuple[str, str]:
    """Find paths to PaperNym GUI and CLI executables."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    installed_gui = Path(local_app_data) / "Programs" / "PaperNym" / "PaperNym.exe"
    installed_cli = Path(local_app_data) / "Programs" / "PaperNym" / "papernym-cli.exe"

    if installed_gui.is_file() and installed_cli.is_file():
        return str(installed_gui), str(installed_cli)

    # Check dist folder
    dist_gui = Path(__file__).resolve().parents[1] / "dist" / "PaperNym" / "PaperNym.exe"
    dist_cli = Path(__file__).resolve().parents[1] / "dist" / "PaperNym" / "papernym-cli.exe"
    if dist_gui.is_file() and dist_cli.is_file():
        return str(dist_gui), str(dist_cli)

    # Fallback to python -m papernym
    cli_on_path = shutil.which("papernym-cli") or shutil.which("papernym") or "papernym"
    gui_on_path = shutil.which("PaperNym") or shutil.which("papernym-gui") or cli_on_path
    return gui_on_path, cli_on_path


def install_windows(gui_path: str, cli_path: str) -> None:
    import winreg

    entries = [
        (
            f"{PDF_KEY_BASE}\\PaperNymRename",
            "Rename with PaperNym",
            f'"{cli_path}" scan "%1"',
            f'"{gui_path}",0',
        ),
        (
            f"{PDF_KEY_BASE}\\PaperNymInspect",
            "Inspect with PaperNym",
            f'"{cli_path}" show "%1"',
            f'"{gui_path}",0',
        ),
        (
            f"{DIR_KEY_BASE}\\PaperNymScan",
            "Rename PDFs with PaperNym",
            f'"{cli_path}" scan "%1"',
            f'"{gui_path}",0',
        ),
        (
            f"{DIR_BG_KEY_BASE}\\PaperNymScan",
            "Rename PDFs with PaperNym",
            f'"{cli_path}" scan "%V"',
            f'"{gui_path}",0',
        ),
    ]

    for key_path, label, command, icon in entries:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, label)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command") as cmd_key:
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)

    print("Successfully registered PaperNym Explorer context menu actions (HKCU).")


def uninstall_windows() -> None:
    import winreg

    subkeys = [
        f"{PDF_KEY_BASE}\\PaperNymRename",
        f"{PDF_KEY_BASE}\\PaperNymInspect",
        f"{DIR_KEY_BASE}\\PaperNymScan",
        f"{DIR_BG_KEY_BASE}\\PaperNymScan",
    ]

    for key_path in subkeys:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
        except OSError:
            pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except OSError:
            pass

    print("Successfully removed PaperNym Explorer context menu actions.")


def check_status_windows() -> bool:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{PDF_KEY_BASE}\\PaperNymRename") as key:
            val, _ = winreg.QueryValueEx(key, "")
            print(f"Context menu is registered: {val}")
            return True
    except OSError:
        print("Context menu is not registered.")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install", action="store_true", help="install Explorer context menu entries"
    )
    parser.add_argument(
        "--uninstall", action="store_true", help="remove Explorer context menu entries"
    )
    parser.add_argument("--status", action="store_true", help="check if context menu entries exist")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("Note: Windows context menu registration is only available on win32 platforms.")
        return 0

    if args.uninstall:
        uninstall_windows()
        return 0
    elif args.status:
        check_status_windows()
        return 0
    elif args.install or not any([args.install, args.uninstall, args.status]):
        gui_path, cli_path = find_executables()
        install_windows(gui_path, cli_path)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
