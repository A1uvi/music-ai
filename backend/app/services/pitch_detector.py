import logging
import librosa
import numpy as np
from pathlib import Path
from typing import List, Tuple
import asyncio
import soundfile as sf
from ..models.music import PitchEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Basic Pitch import — graceful fallback to PYIN when absent
# ---------------------------------------------------------------------------
try:
    from basic_pitch.inference import predict as _bp_predict
    from basic_pitch import ICASSP_2022_MODEL_PATH as _BP_MODEL_PATH
    import pathlib as _pathlib
    # TF 2.16 broke the SavedModel loader ('add_slot' removed). Prefer the ONNX
    # model when onnxruntime is available — it avoids the TF version dependency.
    _ONNX_MODEL_PATH = _pathlib.Path(_BP_MODEL_PATH).with_suffix(".onnx")
    if _ONNX_MODEL_PATH.exists():
        try:
            import onnxruntime  # noqa: F401 — just check it's importable
            _BP_MODEL_PATH = _ONNX_MODEL_PATH
            logger.info("basic-pitch: using ONNX model (onnxruntime)")
        except ImportError:
            logger.info("basic-pitch: onnxruntime absent, using TF SavedModel")
    _BASIC_PITCH_AVAILABLE = True
    logger.info("basic-pitch available — using neural pitch detection")
except ImportError:
    _BASIC_PITCH_AVAILABLE = False
    logger.warning("basic-pitch not installed — falling back to PYIN pitch detection")

# ---------------------------------------------------------------------------
# Optional CREPE import for hybrid pitch refinement (Phase 4)
# ---------------------------------------------------------------------------
try:
    import crepe as _crepe
    _CREPE_AVAILABLE = True
    logger.info("crepe available — hybrid pitch refinement enabled")
except ImportError:
    _CREPE_AVAILABLE = False
    logger.info("crepe not installed — using Basic Pitch without CREPE refinement")

# Minimum Basic Pitch amplitude to accept a note event (Phase 1b)
_MIN_AMPLITUDE = 0.35


class PitchDetector:
    """
    Detects pitches and onsets from audio files.

    Dispatch chain:
      1. Basic Pitch + CREPE → hybrid (best accuracy)
      2. Basic Pitch only
      3. PYIN fallback

    All blocking operations run in a thread pool executor to avoid blocking
    the asyncio event loop. Public interface is unchanged.
    """

    def __init__(self, sample_rate: int = 44100, hop_length: int = 128):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.fmin = librosa.note_to_hz('C2')  # ~65 Hz
        self.fmax = librosa.note_to_hz('C7')  # ~2093 Hz

    async def detect_pitches(self, audio_path: Path) -> Tuple[List[PitchEvent], float, str]:
        """
        Detect pitches from an audio file.

        Returns:
            Tuple of (pitch_events, detected_tempo_bpm, time_signature)
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, self._detect_pitches_sync, audio_path
            )
        except Exception as e:
            raise RuntimeError(f"Pitch detection failed: {str(e)}")

    def _detect_pitches_sync(self, audio_path: Path) -> Tuple[List[PitchEvent], float, str]:
        """Synchronous dispatch — runs in thread pool."""
        from ..utils.music_theory import detect_time_signature

        # Load full signal for tempo + time-sig detection
        y, sr = librosa.load(str(audio_path), sr=self.sample_rate)
        tempo_result, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        tempo = float(np.atleast_1d(tempo_result)[0])
        tempo = max(40.0, min(280.0, tempo))

        # Phase 3b: detect time signature from onset autocorrelation
        time_signature = detect_time_signature(y, sr, tempo)

        harmonic_path: Path | None = None
        try:
            if _BASIC_PITCH_AVAILABLE:
                # Phase 1a: HPSS removes drums/bass before neural pitch detection
                y_harmonic, _ = librosa.effects.hpss(y, margin=3.0)
                harmonic_path = audio_path.parent / (audio_path.stem + '.harmonic.wav')
                sf.write(str(harmonic_path), y_harmonic, sr)

                if _CREPE_AVAILABLE:
                    # Phase 4: hybrid — BP onset boundaries + CREPE pitch correction
                    pitch_events = self._detect_with_hybrid(harmonic_path, y_harmonic, sr)
                else:
                    pitch_events = self._detect_with_basic_pitch(harmonic_path)
            else:
                pitch_events = self._detect_with_pyin(y, sr)
        finally:
            if harmonic_path is not None and harmonic_path.exists():
                try:
                    harmonic_path.unlink()
                except Exception:
                    pass

        return pitch_events, tempo, time_signature

    # ------------------------------------------------------------------
    # Basic Pitch path
    # ------------------------------------------------------------------

    def _detect_with_basic_pitch(self, audio_path: Path) -> List[PitchEvent]:
        """
        Use Spotify Basic Pitch neural model for pitch detection.

        note_events: List[Tuple[start_s, end_s, pitch_midi, amplitude, pitch_bends]]
        """
        _, _, note_events = _bp_predict(str(audio_path), _BP_MODEL_PATH)

        pitch_events: List[PitchEvent] = []
        for event in note_events:
            start_s, end_s, pitch_midi, amplitude, *_ = event
            # Phase 1b: skip low-confidence events
            if float(amplitude) < _MIN_AMPLITUDE:
                continue
            duration = float(end_s) - float(start_s)
            if duration < 0.05:  # skip sub-50ms artifacts
                continue
            frequency = float(librosa.midi_to_hz(int(pitch_midi)))
            pitch_events.append(PitchEvent(
                frequency=frequency,
                start_time=float(start_s),
                duration=duration,
                confidence=float(amplitude),
            ))

        return pitch_events

    # ------------------------------------------------------------------
    # CREPE hybrid path (Phase 4)
    # ------------------------------------------------------------------

    def _detect_with_hybrid(
        self, audio_path: Path, y: np.ndarray, sr: int
    ) -> List[PitchEvent]:
        """
        Hybrid: Basic Pitch for note onset/offset boundaries + CREPE for pitch
        correction within those boundaries.

        Basic Pitch excels at detecting when notes start and stop; CREPE excels
        at accurate frame-level pitch estimation and avoids BP's semitone-snap bias.
        """
        # 1. Basic Pitch for segment boundaries
        bp_events = self._detect_with_basic_pitch(audio_path)
        if not bp_events:
            return []

        # 2. CREPE frame-level pitch tracking (tiny model, 10 ms steps)
        try:
            time_arr, freq_arr, conf_arr, _ = _crepe.predict(
                y, sr,
                model_capacity='tiny',
                viterbi=True,
                step_size=10,
                verbose=0,
            )
        except Exception as e:
            logger.warning(f"CREPE prediction failed ({e}); falling back to Basic Pitch")
            return bp_events

        refined: List[PitchEvent] = []
        for event in bp_events:
            mask = (time_arr >= event.start_time) & (
                time_arr <= event.start_time + event.duration
            )
            if not np.any(mask):
                refined.append(event)
                continue

            window_freqs = freq_arr[mask]
            window_confs = conf_arr[mask]
            total_conf = window_confs.sum()

            if total_conf > 0 and np.any(window_freqs > 0):
                # Confidence-weighted median of CREPE pitches in this window
                valid = window_freqs > 0
                wf = window_freqs[valid]
                wc = window_confs[valid]
                sorted_idx = np.argsort(wf)
                cum = np.cumsum(wc[sorted_idx])
                median_idx = int(np.searchsorted(cum, cum[-1] / 2))
                refined_freq = float(wf[sorted_idx[min(median_idx, len(wf) - 1)]])
            else:
                refined_freq = event.frequency

            refined.append(PitchEvent(
                frequency=refined_freq if refined_freq > 0 else event.frequency,
                start_time=event.start_time,
                duration=event.duration,
                confidence=event.confidence,
            ))

        return refined

    # ------------------------------------------------------------------
    # PYIN fallback path
    # ------------------------------------------------------------------

    def _detect_with_pyin(self, y: np.ndarray, sr: int) -> List[PitchEvent]:
        """Improved PYIN fallback with tighter confidence thresholds."""
        # Harmonic-percussive separation for cleaner melody
        y_harmonic, _ = librosa.effects.hpss(y)

        # Onset detection on the full signal (catches transients better)
        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=sr,
            hop_length=self.hop_length,
            backtrack=True,
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)

        # Probabilistic YIN pitch tracking on harmonic component
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y_harmonic,
            fmin=self.fmin,
            fmax=self.fmax,
            sr=sr,
            hop_length=self.hop_length,
        )

        times = librosa.frames_to_time(
            np.arange(len(f0)), sr=sr, hop_length=self.hop_length
        )

        return self._extract_pitch_events(
            f0, voiced_flag, voiced_probs, times, onset_times,
            confidence_threshold=0.5,  # raised from 0.4 — reduces false positives
            min_duration=0.05,         # raised from 0.03 — 50ms minimum
        )

    def _extract_pitch_events(
        self,
        f0: np.ndarray,
        voiced_flag: np.ndarray,
        voiced_probs: np.ndarray,
        times: np.ndarray,
        onset_times: np.ndarray,
        confidence_threshold: float = 0.5,
        min_duration: float = 0.05,
    ) -> List[PitchEvent]:
        """Extract discrete pitch events from frame-level PYIN output."""
        pitch_events: List[PitchEvent] = []
        current_pitch = None
        current_start = None
        current_freqs: List[float] = []

        sentinel = times[-1] if len(times) > 0 else 0.0
        onset_times = np.append(onset_times, sentinel)
        onset_idx = 0

        def _commit(end_time: float, prob_slice_start: int, prob_slice_end: int):
            duration = end_time - current_start
            if duration >= min_duration and current_freqs:
                avg_freq = float(np.median(current_freqs))
                probs = [
                    voiced_probs[j]
                    for j in range(
                        max(0, prob_slice_start),
                        min(len(voiced_probs), prob_slice_end),
                    )
                    if voiced_probs[j] >= confidence_threshold
                ]
                conf = float(np.mean(probs)) if probs else 0.0
                pitch_events.append(PitchEvent(
                    frequency=avg_freq,
                    start_time=float(current_start),
                    duration=float(duration),
                    confidence=conf,
                ))

        frame_idx = 0
        for freq, voiced, prob, time in zip(f0, voiced_flag, voiced_probs, times):
            if not voiced or prob < confidence_threshold or np.isnan(freq):
                if current_pitch is not None:
                    _commit(time, frame_idx - len(current_freqs), frame_idx)
                    current_pitch = None
                    current_freqs = []
                frame_idx += 1
                continue

            while onset_idx < len(onset_times) - 1 and time >= onset_times[onset_idx + 1]:
                if current_pitch is not None and current_freqs:
                    _commit(onset_times[onset_idx + 1],
                            frame_idx - len(current_freqs), frame_idx)
                    current_pitch = None
                    current_freqs = []
                onset_idx += 1

            if current_pitch is None:
                current_pitch = freq
                current_start = time
                current_freqs = [freq]
            else:
                semitone_diff = abs(12.0 * np.log2(freq / current_pitch))
                if semitone_diff > 2.0:
                    _commit(time, frame_idx - len(current_freqs), frame_idx)
                    current_pitch = freq
                    current_start = time
                    current_freqs = [freq]
                else:
                    current_freqs.append(freq)

            frame_idx += 1

        if current_pitch is not None and current_freqs:
            end = times[-1] if len(times) > 0 else 0.0
            _commit(end, frame_idx - len(current_freqs), frame_idx)

        return pitch_events
