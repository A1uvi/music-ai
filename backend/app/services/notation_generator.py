from typing import List, Dict, Any
import numpy as np
from ..models.music import MusicalNote
from ..models.responses import VexFlowData, VexFlowMeasure, MusicMetadata

# Krumhansl-Kessler tonal hierarchy profiles
_KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# Preferred key spellings for each pitch class (enharmonic-aware)
_KEY_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

_NOTE_TO_PC: Dict[str, int] = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11,
}

_DURATION_BEATS: Dict[str, float] = {
    'w': 4.0, 'hd': 3.0, 'h': 2.0, 'qd': 1.5,
    'q': 1.0, '8d': 0.75, '8': 0.5, '16': 0.25,
}


def _duration_beats(duration: str) -> float:
    """Return beat value for a duration string, stripping rest suffix."""
    return _DURATION_BEATS.get(duration.replace('r', ''), 1.0)


class NotationGenerator:
    """Generates VexFlow-compatible sheet music notation from musical notes."""

    def __init__(self, time_signature: str = "4/4"):
        self.time_signature = time_signature
        self.beats_per_measure = self._parse_time_signature(time_signature)

    def _parse_time_signature(self, time_sig: str) -> float:
        numerator, denominator = map(int, time_sig.split('/'))
        return numerator * (4 / denominator)

    async def generate_vexflow_data(
        self,
        notes: List[MusicalNote],
        tempo: int = 120
    ) -> tuple[VexFlowData, MusicMetadata]:
        if not notes:
            return self._empty_result(tempo)

        key_signature = self._detect_key_signature(notes)
        measures = self._group_into_measures(notes)

        vexflow_measures = []
        for measure_notes in measures:
            vexflow_notes = []
            for note in measure_notes:
                is_rest = note.quantized_note == 'rest'
                vexflow_notes.append({
                    'keys': ['b/4'] if is_rest else [f"{note.pitch}/{note.octave}"],
                    'duration': note.duration,  # already has 'r' suffix for rests
                })
            vexflow_measures.append(VexFlowMeasure(notes=vexflow_notes))

        clef = self._determine_clef(notes)

        vexflow_data = VexFlowData(
            measures=vexflow_measures,
            clef=clef,
            key=key_signature
        )

        beat_dur = 60.0 / tempo
        total_duration = max(
            note.start_time + _duration_beats(note.duration) * beat_dur
            for note in notes
        ) if notes else 0.0

        # Count only pitched notes in metadata
        pitched_count = sum(1 for n in notes if n.quantized_note != 'rest')

        metadata = MusicMetadata(
            tempo=tempo,
            time_signature=self.time_signature,
            key_signature=key_signature,
            total_duration=total_duration,
            note_count=pitched_count
        )

        return vexflow_data, metadata

    def _detect_key_signature(self, notes: List[MusicalNote]) -> str:
        """
        Detect key signature using the Krumhansl-Schmuckler algorithm.

        Correlates the piece's pitch-class histogram against all 24 major/minor
        key profiles and returns the best-matching tonic.
        """
        if not notes:
            return "C"

        # Build pitch-class histogram from pitched notes only
        pc_histogram = np.zeros(12)
        for note in notes:
            if note.quantized_note != 'rest':
                pc = _NOTE_TO_PC.get(note.pitch, 0)
                weight = _DURATION_BEATS.get(note.duration.replace('r', ''), 1.0)
                pc_histogram[pc] += weight

        if pc_histogram.sum() == 0:
            return "C"

        best_corr = -np.inf
        best_key = 'C'

        for i in range(12):
            for profile in (_KK_MAJOR, _KK_MINOR):
                rotated = np.roll(profile, -i)
                if pc_histogram.std() > 0:
                    corr = float(np.corrcoef(pc_histogram, rotated)[0, 1])
                else:
                    corr = 0.0
                if corr > best_corr:
                    best_corr = corr
                    best_key = _KEY_NAMES[i]

        return best_key

    def _group_into_measures(self, notes: List[MusicalNote]) -> List[List[MusicalNote]]:
        """Group notes into measures respecting time signature."""
        measures: List[List[MusicalNote]] = []
        current_measure: List[MusicalNote] = []
        current_beats = 0.0

        for note in notes:
            note_beats = _duration_beats(note.duration)

            if current_beats + note_beats > self.beats_per_measure + 1e-6:
                if current_measure:
                    measures.append(current_measure)
                current_measure = [note]
                current_beats = note_beats
            else:
                current_measure.append(note)
                current_beats += note_beats

        if current_measure:
            measures.append(current_measure)

        return measures if measures else [[]]

    def _determine_clef(self, notes: List[MusicalNote]) -> str:
        """Choose clef based on average octave of pitched notes."""
        pitched = [n for n in notes if n.quantized_note != 'rest']
        if not pitched:
            return "treble"

        avg_octave = sum(n.octave for n in pitched) / len(pitched)
        return "bass" if avg_octave <= 2 else "treble"

    def _empty_result(self, tempo: int = 120) -> tuple[VexFlowData, MusicMetadata]:
        vexflow_data = VexFlowData(measures=[], clef="treble", key="C")
        metadata = MusicMetadata(
            tempo=tempo,
            time_signature=self.time_signature,
            key_signature="C",
            total_duration=0.0,
            note_count=0
        )
        return vexflow_data, metadata
