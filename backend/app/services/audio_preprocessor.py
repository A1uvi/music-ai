"""
Phase 2a — Stationary noise reduction using noisereduce.

Reduces ambient/recording noise before pitch detection by computing a
stationary noise profile from the first 0.5 s of the audio and applying
spectral subtraction.  Falls back to the original file if noisereduce is
not installed or encounters an error.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import noisereduce as _nr
    _NR_AVAILABLE = True
except ImportError:
    _NR_AVAILABLE = False
    logger.info("noisereduce not installed — noise reduction step will be skipped")


class AudioPreprocessor:
    """Applies stationary noise reduction to an audio file."""

    @staticmethod
    def preprocess(audio_path: Path, sample_rate: int = 44100) -> Path:
        """
        Denoise *audio_path* and write the result to a sibling *.denoised.wav*
        file.  Returns the denoised path on success, or *audio_path* unchanged
        if noisereduce is unavailable or the operation fails.

        Args:
            audio_path:  Source audio file.
            sample_rate: Target sample rate for loading.

        Returns:
            Path to the denoised file (or the original if skipped).
        """
        if not _NR_AVAILABLE:
            return audio_path

        import librosa
        import soundfile as sf
        import numpy as np

        try:
            y, sr = librosa.load(str(audio_path), sr=sample_rate)

            # Use the first 0.5 s as a stationary noise profile
            noise_frames = int(0.5 * sr)
            noise_clip = y[:noise_frames] if len(y) > noise_frames else y

            y_denoised = _nr.reduce_noise(
                y=y,
                sr=sr,
                y_noise=noise_clip,
                prop_decrease=0.75,
            )

            output_path = audio_path.parent / (audio_path.stem + '.denoised.wav')
            sf.write(str(output_path), y_denoised, sr)
            logger.debug(f"Noise reduction complete: {output_path}")
            return output_path

        except Exception as exc:
            logger.warning(f"Noise reduction failed ({exc}); using original audio")
            return audio_path
