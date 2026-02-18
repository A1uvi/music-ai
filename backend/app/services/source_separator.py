"""
Phase 2b — Melody source separation using demucs (htdemucs model).

Separates vocals + other stems from drums + bass, sums them into a melody
track, and normalises the output to 0.95 peak amplitude.  The model is lazy-
loaded on first use (approx. 700 MB download on first run).

Falls back to the original file when demucs is not installed or the GPU/CPU
inference fails.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import demucs  # noqa: F401 — check importability
    _DEMUCS_AVAILABLE = True
except ImportError:
    _DEMUCS_AVAILABLE = False
    logger.info("demucs not installed — source separation step will be skipped")


class SourceSeparator:
    """Extracts a melody stem (vocals + other) from a mixed audio file."""

    _model = None  # lazy singleton

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            from demucs.pretrained import get_model
            cls._model = get_model('htdemucs')
            logger.info("demucs htdemucs model loaded")
        return cls._model

    @classmethod
    def separate_melody(cls, audio_path: Path) -> Path:
        """
        Run htdemucs on *audio_path* and return a path to the melody stem
        (vocals + other, normalised to 0.95 peak).

        Returns *audio_path* unchanged if demucs is unavailable or fails.
        """
        if not _DEMUCS_AVAILABLE:
            return audio_path

        import numpy as np

        try:
            import torch
            import torchaudio
            import soundfile as sf
            from demucs.apply import apply_model

            model = cls._get_model()
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = model.to(device)

            # Load audio and resample to model's expected rate if necessary
            wav, file_sr = torchaudio.load(str(audio_path))
            if file_sr != model.samplerate:
                wav = torchaudio.functional.resample(wav, file_sr, model.samplerate)

            # Ensure stereo (demucs always expects 2 channels)
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)
            elif wav.shape[0] > 2:
                wav = wav[:2]

            wav = wav.to(device)

            # Run separation — returns (batch, stems, channels, time)
            with torch.no_grad():
                sources = apply_model(model, wav.unsqueeze(0))[0]

            # Identify stem indices (htdemucs: drums, bass, other, vocals)
            names = list(model.sources)
            vocal_idx = names.index('vocals') if 'vocals' in names else None
            other_idx = names.index('other') if 'other' in names else None

            parts = []
            if vocal_idx is not None:
                parts.append(sources[vocal_idx])
            if other_idx is not None:
                parts.append(sources[other_idx])

            if not parts:
                logger.warning("demucs: no vocals/other stems found; using original audio")
                return audio_path

            melody = sum(parts)  # (channels, time)

            # Normalise to 0.95 peak
            peak = melody.abs().max()
            if peak > 0:
                melody = melody * (0.95 / peak)

            # Convert to mono for downstream pitch detection
            melody_mono = melody.mean(dim=0).cpu().numpy()

            output_path = audio_path.parent / (audio_path.stem + '.melody.wav')
            sf.write(str(output_path), melody_mono, model.samplerate)
            logger.debug(f"Source separation complete: {output_path}")
            return output_path

        except Exception as exc:
            logger.warning(f"Source separation failed ({exc}); using original audio")
            return audio_path
