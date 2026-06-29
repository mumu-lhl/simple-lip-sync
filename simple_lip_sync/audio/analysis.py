"""Standard-library audio analysis for lip sync generation."""

import array
import math
import os
import wave

from ..core.viseme_curve import (
    FORMANT_PROTOTYPES,
    compute_openness,
    score_visemes_from_formant_energy,
    zero_weights,
)
from . import native_backend


def analyze_wav(audio_path, db_threshold=-50.0, rms_threshold=0.01):
    """Return timestamped viseme samples from a mono or stereo PCM WAV file."""
    samples, sample_rate = load_wav_samples(audio_path)
    return analyze_samples(samples, sample_rate, db_threshold, rms_threshold)


def analyze_samples(samples, sample_rate, db_threshold=-50.0, rms_threshold=0.01):
    """Return timestamped viseme samples from normalized mono float samples."""
    if not samples:
        return []

    try:
        return native_backend.analyze_samples(
            samples,
            sample_rate,
            db_threshold=db_threshold,
            rms_threshold=rms_threshold,
        )
    except RuntimeError:
        pass

    return analyze_samples_python(samples, sample_rate, db_threshold, rms_threshold)


def analyze_samples_python(
    samples, sample_rate, db_threshold=-50.0, rms_threshold=0.01
):
    """Return timestamped viseme samples with the pure Python analyzer."""
    frame_length = max(512, int(sample_rate * 0.064))
    hop_length = max(80, int(sample_rate * 0.010))
    if len(samples) < frame_length:
        samples = samples + [0.0] * (frame_length - len(samples))

    window = _hann_window(frame_length)
    formant_frequencies = sorted(
        {prototype["f1"] for prototype in FORMANT_PROTOTYPES.values()}
        | {prototype["f2"] for prototype in FORMANT_PROTOTYPES.values()}
    )

    results = []
    for start in range(0, len(samples) - frame_length + 1, hop_length):
        frame = samples[start : start + frame_length]
        windowed = [frame[index] * window[index] for index in range(frame_length)]
        frame_rms = math.sqrt(sum(value * value for value in windowed) / frame_length)
        frame_db = 20 * math.log10(frame_rms + 1e-10)
        openness = compute_openness(frame_db, frame_rms, db_threshold, rms_threshold)
        timestamp = round((start + (frame_length / 2.0)) / sample_rate, 4)

        weights = zero_weights()
        if openness > 1e-3:
            energy = {
                frequency: _goertzel_power(windowed, sample_rate, frequency)
                for frequency in formant_frequencies
            }
            weights = score_visemes_from_formant_energy(energy)

        results.append(
            {
                "time": timestamp,
                "openness": round(openness, 4),
                "weights": weights,
            }
        )
    return results


def load_wav_samples(audio_path):
    """Load PCM WAV samples as normalized mono floats."""
    with wave.open(audio_path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()
        raw = wav_file.readframes(frame_count)

    values = _decode_pcm(raw, sample_width)
    if channels > 1:
        mono = []
        for index in range(0, len(values), channels):
            frame = values[index : index + channels]
            mono.append(sum(frame) / len(frame))
        values = mono
    return values, sample_rate


def cleanup_temp_file(path, is_temp):
    """Remove a temporary audio file if requested."""
    if is_temp and path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _decode_pcm(raw, sample_width):
    if sample_width == 1:
        return [(value - 128) / 128.0 for value in raw]

    if sample_width == 2:
        values = array.array("h")
        values.frombytes(raw)
        if _needs_byteswap():
            values.byteswap()
        return [max(-1.0, min(1.0, value / 32768.0)) for value in values]

    if sample_width == 3:
        values = []
        for index in range(0, len(raw), 3):
            chunk = raw[index : index + 3]
            if len(chunk) < 3:
                break
            sign = b"\xff" if chunk[2] & 0x80 else b"\x00"
            value = int.from_bytes(chunk + sign, byteorder="little", signed=True)
            values.append(max(-1.0, min(1.0, value / 8388608.0)))
        return values

    if sample_width == 4:
        values = array.array("i")
        values.frombytes(raw)
        if _needs_byteswap():
            values.byteswap()
        return [max(-1.0, min(1.0, value / 2147483648.0)) for value in values]

    raise ValueError(f"Unsupported WAV sample width: {sample_width}")


def _needs_byteswap():
    return array.array("h", [1]).tobytes() != b"\x01\x00"


def _hann_window(size):
    if size <= 1:
        return [1.0]
    return [
        0.5 - (0.5 * math.cos((2.0 * math.pi * index) / (size - 1)))
        for index in range(size)
    ]


def _goertzel_power(samples, sample_rate, frequency):
    omega = (2.0 * math.pi * frequency) / sample_rate
    coefficient = 2.0 * math.cos(omega)
    previous = 0.0
    previous2 = 0.0
    for sample in samples:
        current = sample + (coefficient * previous) - previous2
        previous2 = previous
        previous = current
    power = (
        (previous2 * previous2)
        + (previous * previous)
        - (coefficient * previous * previous2)
    )
    return max(0.0, power / max(1, len(samples)))
