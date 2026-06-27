"""FFmpeg discovery and audio conversion."""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


def convert_to_wav_16000(audio_path):
    """Convert an audio file to a temporary 16 kHz mono PCM WAV.

    If FFmpeg is unavailable and the input is already a WAV file, the original
    path is returned. The caller must only delete the result when ``is_temp`` is
    true.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Input file does not exist: {audio_path}")

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        if Path(audio_path).suffix.lower() == ".wav":
            return audio_path, False
        raise FileNotFoundError(
            "FFmpeg was not found. Install FFmpeg, put it on PATH, or bundle it "
            "under simple_lip_sync/audio/lib."
        )

    base_name = Path(audio_path).stem
    fd, output_path = tempfile.mkstemp(prefix=f"{base_name}_sls16khz_", suffix=".wav")
    os.close(fd)

    command = [
        ffmpeg_path,
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
        "-y",
        output_path,
    ]

    try:
        subprocess.run(command, check=True, timeout=1800, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise RuntimeError(f"FFmpeg failed: {stderr}") from exc

    return output_path, True


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
                    os.chmod(candidate, 0o755)
                except OSError as exc:
                    raise PermissionError(
                        f"Failed to make FFmpeg executable at {candidate}"
                    ) from exc
            return candidate

    return shutil.which("ffmpeg")

