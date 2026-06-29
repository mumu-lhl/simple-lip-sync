"""FFmpeg discovery and audio conversion."""

import hashlib
import os
import platform
import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path


_WAV_CACHE = {}
_CACHE_DIR = os.path.join(tempfile.gettempdir(), "simple_lip_sync")


def _get_cache_key(audio_path, seek_seconds=0.0, duration_seconds=0.0):
    abs_path = os.path.abspath(audio_path)
    stat = os.stat(abs_path)
    raw_key = f"{abs_path}|{stat.st_size}|{stat.st_mtime_ns}"
    if seek_seconds or duration_seconds:
        raw_key += f"|{seek_seconds:.4f}|{duration_seconds:.4f}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _ensure_cache_dir():
    os.makedirs(_CACHE_DIR, exist_ok=True)


def convert_to_wav_16000(audio_path, seek_seconds=0.0, duration_seconds=0.0):
    """Convert an audio file to a cached 16 kHz mono PCM WAV.

    If FFmpeg is unavailable and the input is already a WAV file, the original
    path is returned. Otherwise the result is cached in the system temporary
    directory and returned with ``is_temp=False``.

    The cache key is derived from the absolute path, file size and modification
    timestamp, so replacing the source file automatically produces a fresh cache
    entry on the next call.

    When *seek_seconds* is non-zero, the audio is skipped forward by that many
    seconds before conversion.  When *duration_seconds* is non-zero, only that
    many seconds of audio are kept.  Both values are included in the cache key.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Input file does not exist: {audio_path}")

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        if seek_seconds > 0 or duration_seconds > 0:
            raise FileNotFoundError(
                "FFmpeg is required for audio trimming but was not found."
            )
        if Path(audio_path).suffix.lower() == ".wav":
            return audio_path, False
        raise FileNotFoundError(
            "FFmpeg was not found. Install FFmpeg, put it on PATH, or bundle it "
            "under simple_lip_sync/audio/lib."
        )

    cache_key = _get_cache_key(audio_path, seek_seconds, duration_seconds)

    cached_path = _WAV_CACHE.get(cache_key)
    if cached_path and os.path.isfile(cached_path):
        return cached_path, False

    _ensure_cache_dir()
    output_path = os.path.join(_CACHE_DIR, f"sls16khz_{cache_key}.wav")

    if os.path.isfile(output_path):
        _WAV_CACHE[cache_key] = output_path
        return output_path, False

    command = [ffmpeg_path]
    if seek_seconds > 0:
        command.extend(["-ss", str(seek_seconds)])
    command.extend([
        "-i",
        audio_path,
        "-max_muxing_queue_size",
        "1024",
        "-threads",
        str(os.cpu_count() or 2),
        "-af",
        "loudnorm=I=-14:LRA=11:TP=-1.5",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-sample_fmt",
        "s16",
    ])
    if duration_seconds > 0:
        command.extend(["-t", str(duration_seconds)])
    command.extend(["-y", output_path])

    try:
        subprocess.run(  # nosec B603
            command,
            check=True,
            timeout=1800,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise RuntimeError(f"FFmpeg failed: {stderr}") from exc

    _WAV_CACHE[cache_key] = output_path
    return output_path, False


def clear_wav_cache():
    """Remove all cached WAV files and clear the in-memory index."""
    global _WAV_CACHE
    _WAV_CACHE = {}
    if os.path.isdir(_CACHE_DIR):
        for entry in os.listdir(_CACHE_DIR):
            if entry.startswith("sls16khz_") and entry.endswith(".wav"):
                try:
                    os.remove(os.path.join(_CACHE_DIR, entry))
                except OSError:
                    pass


def find_ffmpeg():
    """Find a bundled or system FFmpeg executable."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    executable = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    candidates = [
        os.path.join(script_dir, "lib", executable),
        os.path.join(script_dir, "lib", platform.system().lower(), executable),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            if platform.system() != "Windows" and not os.access(candidate, os.X_OK):
                try:
                    os.chmod(candidate, 0o755)  # nosec B103
                except OSError as exc:
                    raise PermissionError(
                        f"Failed to make FFmpeg executable at {candidate}"
                    ) from exc
            return candidate

    return shutil.which("ffmpeg")
