"""Package Simple Lip Sync release archives."""

from __future__ import annotations

import argparse
import os
import stat
import zipfile
from pathlib import Path


ROOT = Path("simple_lip_sync")
EXCLUDED_DIRS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffmpeg-arcname", default="simple_lip_sync/audio/lib/ffmpeg")
    parser.add_argument("--ffmpeg-source-url")
    parser.add_argument("--native-library")
    parser.add_argument("--native-arcname")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        _write_addon_files(archive)
        if args.ffmpeg:
            _write_ffmpeg(archive, Path(args.ffmpeg), args.ffmpeg_arcname)
            if args.ffmpeg_source_url:
                _write_ffmpeg_notice(archive, args.ffmpeg_source_url)
        if args.native_library:
            if not args.native_arcname:
                raise ValueError("--native-arcname is required with --native-library")
            _write_native_library(
                archive, Path(args.native_library), args.native_arcname
            )


def _write_addon_files(archive: zipfile.ZipFile) -> None:
    for current_root, dirs, files in os.walk(ROOT):
        current_path = Path(current_root)
        dirs[:] = [
            name
            for name in dirs
            if name not in EXCLUDED_DIRS
            and (current_path / name) != ROOT / "audio" / "lib"
            and (current_path / name) != ROOT / "audio" / "native"
        ]
        for file_name in files:
            path = current_path / file_name
            if path.suffix in EXCLUDED_SUFFIXES:
                continue
            archive.write(path, path.as_posix())


def _write_ffmpeg(
    archive: zipfile.ZipFile,
    ffmpeg_path: Path,
    arcname: str,
) -> None:
    if not ffmpeg_path.is_file():
        raise FileNotFoundError(ffmpeg_path)

    info = zipfile.ZipInfo.from_file(ffmpeg_path, arcname)
    if not arcname.endswith(".exe"):
        info.external_attr = (stat.S_IFREG | 0o755) << 16
    with ffmpeg_path.open("rb") as file:
        archive.writestr(info, file.read(), compress_type=zipfile.ZIP_DEFLATED)


def _write_ffmpeg_notice(archive: zipfile.ZipFile, source_url: str) -> None:
    notice = (
        "This package bundles an FFmpeg executable for user convenience.\n"
        "FFmpeg is licensed separately by the FFmpeg project and its build provider.\n"
        f"Build source URL: {source_url}\n"
    )
    archive.writestr("simple_lip_sync/audio/lib/FFMPEG_NOTICE.txt", notice)


def _write_native_library(
    archive: zipfile.ZipFile,
    library_path: Path,
    arcname: str,
) -> None:
    if not library_path.is_file():
        raise FileNotFoundError(library_path)

    info = zipfile.ZipInfo.from_file(library_path, arcname)
    if not arcname.endswith(".dll"):
        info.external_attr = (stat.S_IFREG | 0o755) << 16
    with library_path.open("rb") as file:
        archive.writestr(info, file.read(), compress_type=zipfile.ZIP_DEFLATED)


if __name__ == "__main__":
    main()
