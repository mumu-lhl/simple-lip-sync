"""Copy the local native audio backend into the add-on package tree."""

import argparse
import platform
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crate", default="native/simple_lip_sync_audio")
    parser.add_argument("--addon-dir", default="simple_lip_sync")
    args = parser.parse_args()

    crate_dir = Path(args.crate)
    addon_dir = Path(args.addon_dir)
    library_name, platform_dir = _native_library_target()
    source = crate_dir / "target" / "release" / library_name
    target = addon_dir / "audio" / "native" / platform_dir / library_name

    if not source.is_file():
        raise SystemExit(f"Native library does not exist: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"Copied {source} -> {target}")


def _native_library_target():
    system = platform.system()
    arch = _platform_arch()

    if system == "Windows":
        return "simple_lip_sync_audio.dll", f"windows-{arch}"
    if system == "Darwin":
        return "libsimple_lip_sync_audio.dylib", f"macos-{arch}"
    if system == "Linux":
        return "libsimple_lip_sync_audio.so", f"linux-{arch}"

    raise SystemExit(f"Unsupported platform: {system}")


def _platform_arch():
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"amd64", "x86_64", "x64"}:
        return "x64"
    return machine.replace("-", "_")


if __name__ == "__main__":
    main()
