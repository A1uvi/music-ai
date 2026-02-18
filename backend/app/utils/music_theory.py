import librosa
import numpy as np
from typing import List, Tuple


def frequency_to_midi(frequency: float) -> int:
    """Convert frequency in Hz to MIDI note number."""
    if frequency <= 0:
        return 0
    return int(round(librosa.hz_to_midi(frequency)))


def midi_to_note_name(midi_note: int) -> Tuple[str, int]:
    """
    Convert MIDI note number to note name and octave.

    Returns:
        Tuple of (note_name, octave) e.g., ("C#", 4)
    """
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note = note_names[midi_note % 12]
    return note, octave


def note_name_to_midi(note_name: str, octave: int = 4) -> int:
    """
    Convert note name and octave to MIDI note number.

    Args:
        note_name: Note name like "C", "C#", "Db"
        octave: Octave number (default 4 for middle octave)
    """
    note_map = {
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4,
        'F': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11
    }

    if note_name not in note_map:
        raise ValueError(f"Invalid note name: {note_name}")

    return (octave + 1) * 12 + note_map[note_name]


def get_allowed_midi_notes(allowed_notes: List[str]) -> List[int]:
    """
    Generate all MIDI note numbers for allowed notes across all octaves.

    Args:
        allowed_notes: List of note names like ["C", "D#", "E"]

    Returns:
        Sorted list of MIDI note numbers
    """
    midi_notes = []

    # Generate notes across reasonable octave range (C0 to C8)
    for octave in range(9):
        for note_name in allowed_notes:
            try:
                midi_note = note_name_to_midi(note_name, octave)
                if 0 <= midi_note <= 127:
                    midi_notes.append(midi_note)
            except ValueError:
                continue

    return sorted(set(midi_notes))


def find_nearest_allowed_note(midi_note: int, allowed_midi_notes: List[int]) -> int:
    """
    Find the nearest allowed MIDI note to the given MIDI note.

    Args:
        midi_note: Target MIDI note number
        allowed_midi_notes: List of allowed MIDI note numbers

    Returns:
        Nearest allowed MIDI note number
    """
    if not allowed_midi_notes:
        return midi_note

    # Find nearest note by minimum distance
    distances = [abs(midi_note - allowed) for allowed in allowed_midi_notes]
    min_idx = np.argmin(distances)

    return allowed_midi_notes[min_idx]


def quantize_duration(duration_seconds: float, tempo: int = 120) -> str:
    """
    Quantize a duration in seconds to nearest musical note value (greedy).

    Used for rest insertion; pitched note durations use quantize_sequence_viterbi.
    """
    beat_duration = 60.0 / tempo

    note_values = {
        'w': 4.0,
        'hd': 3.0,
        'h': 2.0,
        'qd': 1.5,
        'q': 1.0,
        '8d': 0.75,
        '8': 0.5,
        '16': 0.25,
    }

    duration_beats = duration_seconds / beat_duration

    best_match = 'q'
    min_diff = float('inf')

    for notation, beats in note_values.items():
        diff = abs(duration_beats - beats)
        if diff < min_diff:
            min_diff = diff
            best_match = notation

    return best_match


# ---------------------------------------------------------------------------
# Phase 3a — Viterbi DP duration quantization
# ---------------------------------------------------------------------------

_DURATION_GRID: List[Tuple[str, float]] = [
    ('16', 0.25),
    ('8',  0.5),
    ('8d', 0.75),
    ('q',  1.0),
    ('qd', 1.5),
    ('h',  2.0),
    ('hd', 3.0),
    ('w',  4.0),
]

_GRID_UNIT = 0.25  # 16th-note grid in quarter-beat units


def quantize_sequence_viterbi(
    durations_beats: List[float],
    beats_per_measure: float,
) -> List[str]:
    """
    Quantize a sequence of note durations using Viterbi DP so that notes land
    cleanly on beat boundaries across the full sequence, instead of greedily
    per-note.

    State:  beat position within the current measure, discretised to a
            16th-note grid (0.25 beats per cell).
    Cost:   |actual_beats - candidate_beats| + 0.05 for landing off a
            quarter-note beat.

    Args:
        durations_beats: List of real-valued note durations in quarter beats.
        beats_per_measure: Quarter beats per measure (e.g. 4.0 for 4/4,
                           3.0 for 3/4 or 6/8).

    Returns:
        List of duration strings (same length as input).
    """
    n = len(durations_beats)
    if n == 0:
        return []

    # Number of grid positions per measure
    max_pos = max(1, int(round(beats_per_measure / _GRID_UNIT)))
    # Grid positions per quarter-note beat (for off-beat penalty)
    beat_unit = max(1, int(round(1.0 / _GRID_UNIT)))  # = 4

    INF = float('inf')
    # dp[i][pos] = minimum accumulated cost after quantizing the first i notes,
    #              landing at measure position pos.
    dp = [[INF] * max_pos for _ in range(n + 1)]
    # back[i][pos] = (prev_pos, dur_grid_index) that achieved dp[i][pos]
    back: List[List[tuple | None]] = [[None] * max_pos for _ in range(n + 1)]

    dp[0][0] = 0.0  # always start at beat 0 of the measure

    for i in range(n):
        actual = durations_beats[i]
        for pos in range(max_pos):
            if dp[i][pos] == INF:
                continue
            for j, (dur_name, dur_beats) in enumerate(_DURATION_GRID):
                quant_err = abs(actual - dur_beats)
                dur_grids = int(round(dur_beats / _GRID_UNIT))
                next_pos = (pos + dur_grids) % max_pos
                # Small penalty for landing off a quarter-note beat
                off_beat = 0.05 if (next_pos % beat_unit != 0) else 0.0
                cost = dp[i][pos] + quant_err + off_beat
                if cost < dp[i + 1][next_pos]:
                    dp[i + 1][next_pos] = cost
                    back[i + 1][next_pos] = (pos, j)

    # Find best terminal position (prefer position 0 = clean measure boundary)
    best_end = int(np.argmin(dp[n]))

    # Traceback
    result: List[str] = ['q'] * n
    pos = best_end
    for i in range(n, 0, -1):
        entry = back[i][pos]
        if entry is None:
            pos = 0
            continue
        prev_pos, dur_idx = entry
        result[i - 1] = _DURATION_GRID[dur_idx][0]
        pos = prev_pos

    return result


# ---------------------------------------------------------------------------
# Phase 3b — Auto time signature detection
# ---------------------------------------------------------------------------

def detect_time_signature(y: np.ndarray, sr: int, tempo: float) -> str:
    """
    Detect the predominant time signature (4/4, 3/4, or 6/8) from audio.

    Uses onset-envelope autocorrelation: strong energy at the 3-beat period
    relative to the 4-beat period suggests triple metre (3/4 or 6/8).

    Args:
        y: Audio signal array.
        sr: Sample rate in Hz.
        tempo: Detected tempo in BPM.

    Returns:
        Time signature string: "4/4", "3/4", or "6/8".
    """
    try:
        _HOP = 512  # hop length used by onset_strength (librosa default)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=_HOP)

        # Number of frames per beat at detected tempo
        beat_frames = sr * 60.0 / (tempo * _HOP)

        # Autocorrelation up to 8 beats ahead
        max_lag = int(round(beat_frames * 8)) + 1
        ac = librosa.autocorrelate(onset_env, max_size=max_lag)

        def _energy_at(period_beats: float) -> float:
            period_f = int(round(beat_frames * period_beats))
            if period_f <= 0 or period_f >= len(ac):
                return 0.0
            # Average over ±25% window to tolerate tempo drift
            window = max(1, int(round(beat_frames * 0.25)))
            lo = max(0, period_f - window)
            hi = min(len(ac), period_f + window + 1)
            return float(np.max(ac[lo:hi]))

        e3 = _energy_at(3.0)
        e4 = _energy_at(4.0)
        e6 = _energy_at(6.0)

        # 3/4 if 3-beat periodicity clearly dominates 4-beat
        if e3 > e4 * 1.15 and e3 >= e6 * 0.85:
            return "3/4"
        # 6/8 if 6-beat periodicity dominates both (characteristic of compound duple)
        if e6 > e4 * 1.25 and e6 > e3 * 1.1:
            return "6/8"
        return "4/4"

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Time signature detection failed ({e}); defaulting to 4/4"
        )
        return "4/4"
