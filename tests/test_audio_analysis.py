"""Tests for standard-library WAV analysis."""

import math
import os
import struct
import tempfile
import unittest
import wave

from simple_lip_sync.audio.analysis import analyze_wav


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
                    value = int(12000 * math.sin(2.0 * math.pi * 850.0 * index / sample_rate))
                    frames.append(struct.pack("<h", value))
                wav_file.writeframes(b"".join(frames))

            samples = analyze_wav(path, db_threshold=-60.0, rms_threshold=0.001)
            self.assertTrue(samples)
            self.assertIn("a", samples[0]["weights"])
            self.assertGreater(max(sample["openness"] for sample in samples), 0.0)


if __name__ == "__main__":
    unittest.main()

