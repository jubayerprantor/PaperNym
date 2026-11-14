import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "build_windows", ROOT / "scripts" / "build_windows.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_version_matches_the_package():
    import papernym

    assert load().version() == papernym.__version__


def test_version_file_has_four_numbers(tmp_path, monkeypatch):
    build = load()
    monkeypatch.setattr(build, "BUILD", tmp_path)
    text = build.version_file("1.2.3").read_text(encoding="utf-8")
    assert "filevers=(1, 2, 3, 0)" in text and "StringStruct('ProductVersion', '1.2.3')" in text


def test_clean_path_keeps_only_python_and_windows(monkeypatch):
    build = load()
    monkeypatch.setenv("PATH", r"C:\Users\me\anaconda3\Library\bin;C:\msys64\usr\bin")
    path = build.clean_path().lower()
    assert "anaconda" not in path and "msys" not in path
    assert str(Path(sys.executable).parent).lower() in path


def test_tag_must_match_version(monkeypatch):
    build = load()
    monkeypatch.setattr(sys, "argv", ["build_windows.py", "--expected-version", "v99.0.0"])
    monkeypatch.setattr(sys, "platform", "win32")
    with pytest.raises(SystemExit, match="version mismatch"):
        build.main()


def test_installer_always_ships_and_registers_the_cli():
    iss = (Path(__file__).resolve().parents[1] / "packaging" / "papernym.iss").read_text(
        encoding="utf-8"
    )
    assert "addtopath" not in iss  # PATH is not optional any more
    path_line = next(
        line for line in iss.splitlines() if 'ValueName: "Path"; ValueData: "{olddata}' in line
    )
    assert "Tasks:" not in path_line
    assert r"App Paths\{#CliExe}" in iss and r"App Paths\{#AppExe}" in iss
    assert '#define CliExe "papernym-cli.exe"' in iss


def test_appimage_setup_appdir(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "build_appimage", ROOT / "scripts" / "build_appimage.py"
    )
    appimage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(appimage)

    appdir = tmp_path / "AppDir"
    appimage.setup_appdir(appdir, "1.2.3")

    assert (appdir / "AppRun").is_file()
    assert (appdir / "papernym.desktop").is_file()
    assert (appdir / "usr" / "bin").is_dir()
    apprun_content = (appdir / "AppRun").read_text(encoding="utf-8")
    assert "papernym-cli" in apprun_content
    assert "PaperNym" in apprun_content


def test_macos_bundle_setup(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "build_macos", ROOT / "scripts" / "build_macos.py"
    )
    macos = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(macos)

    plist = macos.make_info_plist("1.2.3")
    assert plist["CFBundleName"] == "PaperNym"
    assert plist["CFBundleVersion"] == "1.2.3"
    assert plist["CFBundleExecutable"] == "PaperNym"

    bundle = tmp_path / "PaperNym.app"
    macos.setup_macos_bundle(bundle, "1.2.3")
    assert (bundle / "Contents" / "Info.plist").is_file()
    assert (bundle / "Contents" / "MacOS").is_dir()
    assert (bundle / "Contents" / "Resources").is_dir()


def test_install_context_menu_executables():
    spec = importlib.util.spec_from_file_location(
        "install_context_menu", ROOT / "scripts" / "install_context_menu.py"
    )
    menu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(menu)

    gui, cli = menu.find_executables()
    assert gui and cli


def test_packaging_metadata_files_exist():
    homebrew = ROOT / "Formula" / "papernym.rb"
    assert homebrew.is_file()
    assert "class Papernym < Formula" in homebrew.read_text(encoding="utf-8")

    metainfo = ROOT / "packaging" / "io.github.jubayerprantor.PaperNym.metainfo.xml"
    assert metainfo.is_file()
    assert "<id>io.github.jubayerprantor.PaperNym</id>" in metainfo.read_text(encoding="utf-8")

    flatpak = ROOT / "packaging" / "io.github.jubayerprantor.PaperNym.yml"
    assert flatpak.is_file()
    assert "io.github.jubayerprantor.PaperNym" in flatpak.read_text(encoding="utf-8")

    reg = ROOT / "packaging" / "windows_context_menu.reg"
    assert reg.is_file()
    assert "Rename with PaperNym" in reg.read_text(encoding="utf-8")
