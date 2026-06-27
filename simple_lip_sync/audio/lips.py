"""Lip sync generation facade."""

from .analysis import analyze_wav, cleanup_temp_file
from .ffmpeg import convert_to_wav_16000
from ..core.viseme_curve import build_viseme_keyframes


class Lips:
    """Generate sparse viseme keyframes from audio."""

    @staticmethod
    def mmd_lips_gen(
        wav_path,
        buffer=0.05,
        approach_speed=3.0,
        db_threshold=-50.0,
        rms_threshold=0.01,
        max_morph_value=1.0,
        start_frame=1,
        fps=24,
        anticipation_scale=1.0,
    ):
        """Generate sparse viseme keyframes from an input audio file."""
        wav_path_16, is_temp = convert_to_wav_16000(wav_path)
        try:
            viseme_samples = analyze_wav(
                wav_path_16,
                db_threshold=db_threshold,
                rms_threshold=rms_threshold,
            )
        finally:
            cleanup_temp_file(wav_path_16, is_temp)

        return build_viseme_keyframes(
            viseme_samples,
            start_frame=start_frame,
            fps=fps,
            max_morph_value=max_morph_value,
            buffer=buffer,
            approach_speed=approach_speed,
            anticipation_scale=anticipation_scale,
        )

