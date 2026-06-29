"""Tests for standard-library WAV analysis."""

import math
import os
import struct
import tempfile
import unittest
import wave

from simple_lip_sync.audio import native_backend
from simple_lip_sync.audio.analysis import analyze_samples_python, analyze_wav


class AudioAnalysisTests(unittest.TestCase):
    """Audio analysis tests."""

    def test_analyze_wav_returns_viseme_samples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "tone.wav")
            sample_rate = 16000
            duration = 0.12
            with wave.open(path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                frames = []
                for index in range(int(sample_rate * duration)):
                    value = int(
                        12000 * math.sin(2.0 * math.pi * 850.0 * index / sample_rate)
                    )
                    frames.append(struct.pack("<h", value))
                wav_file.writeframes(b"".join(frames))

            samples = analyze_wav(path, db_threshold=-60.0, rms_threshold=0.001)
            self.assertTrue(samples)
            self.assertIn("a", samples[0]["weights"])
            self.assertGreater(max(sample["openness"] for sample in samples), 0.0)

    def test_native_analyzer_matches_python_reference(self):
        if not native_backend.is_available():
            self.skipTest("native audio backend is not available")

        sample_rate = 16000
        samples = []
        for index in range(int(sample_rate * 0.18)):
            if index < sample_rate * 0.04:
                samples.append(0.0)
                continue
            time = index / sample_rate
            value = (
                0.32 * math.sin(2.0 * math.pi * 850.0 * time)
                + 0.21 * math.sin(2.0 * math.pi * 1450.0 * time)
                + 0.11 * math.sin(2.0 * math.pi * 320.0 * time)
            )
            samples.append(value)

        python_samples = analyze_samples_python(
            samples,
            sample_rate,
            db_threshold=-60.0,
            rms_threshold=0.001,
        )
        native_samples = native_backend.analyze_samples(
            samples,
            sample_rate,
            db_threshold=-60.0,
            rms_threshold=0.001,
        )

        self.assertEqual(len(python_samples), len(native_samples))
        for python_sample, native_sample in zip(python_samples, native_samples):
            self.assertAlmostEqual(
                python_sample["time"], native_sample["time"], places=4
            )
            self.assertAlmostEqual(
                python_sample["openness"],
                native_sample["openness"],
                delta=0.001,
            )
            for viseme, python_value in python_sample["weights"].items():
                self.assertAlmostEqual(
                    python_value,
                    native_sample["weights"][viseme],
                    delta=0.001,
                    msg=f"viseme {viseme} at {python_sample['time']}",
                )


if __name__ == "__main__":
    unittest.main()
