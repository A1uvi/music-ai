from typing import List, Optional
from ..models.music import PitchEvent, MusicalNote
from ..utils.music_theory import (
    frequency_to_midi,
    midi_to_note_name,
    get_allowed_midi_notes,
    find_nearest_allowed_note,
    quantize_duration,
    quantize_sequence_viterbi,
)

_DURATION_BEATS = {
    'w': 4.0, 'hd': 3.0, 'h': 2.0, 'qd': 1.5,
    'q': 1.0, '8d': 0.75, '8': 0.5, '16': 0.25,
}


class NoteQuantizer:
    """
    Quantizes detected pitches to allowed musical notes.

    Fills gaps between pitch events with rest notes, uses the detected tempo
    for accurate duration mapping, and applies Viterbi DP to produce note
    durations that fill measures cleanly rather than drifting beat by beat.
    """

    ALL_CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(
        self,
        allowed_notes: Optional[List[str]] = None,
        tempo: float = 120.0,
        time_signature: str = "4/4",
    ):
        if allowed_notes is None:
            allowed_notes = self.ALL_CHROMATIC
        self.allowed_notes = allowed_notes
        self.tempo = tempo
        self.allowed_midi = get_allowed_midi_notes(allowed_notes)

        if not self.allowed_midi:
            raise ValueError("No valid allowed notes provided")

        # Parse time signature for Viterbi DP
        numerator, denominator = map(int, time_signature.split('/'))
        self.beats_per_measure: float = numerator * (4.0 / denominator)

    async def quantize_pitches(
        self,
        pitch_events: List[PitchEvent]
    ) -> List[MusicalNote]:
        """
        Quantize pitch events to musical notes.

        Pass 1: Run Viterbi DP over all pitched-note durations to find a
                globally optimal quantization that keeps notes aligned to
                measure boundaries.
        Pass 2: Reconstruct MusicalNote list, inserting greedy-quantized
                rest notes for silent gaps.
        """
        if not pitch_events:
            return []

        # Sort by start time (pitch detector should already do this, but be safe)
        pitch_events = sorted(pitch_events, key=lambda e: e.start_time)

        beat_duration = 60.0 / self.tempo
        min_rest_seconds = 0.25 * beat_duration

        # --- Pass 1: Viterbi DP on pitched-note durations -----------------
        durations_beats = [e.duration / beat_duration for e in pitch_events]
        viterbi_durations = quantize_sequence_viterbi(durations_beats, self.beats_per_measure)

        # --- Pass 2: build MusicalNote list --------------------------------
        musical_notes: List[MusicalNote] = []

        for i, event in enumerate(pitch_events):
            # Insert rest for gap before this note (still greedy — fine for rests)
            if musical_notes:
                prev = musical_notes[-1]
                prev_dur_key = prev.duration.replace('r', '')
                prev_beats = _DURATION_BEATS.get(prev_dur_key, 1.0)
                prev_end = prev.start_time + prev_beats * beat_duration
                gap = event.start_time - prev_end

                if gap >= min_rest_seconds:
                    rest_dur = quantize_duration(gap, self.tempo)
                    musical_notes.append(MusicalNote(
                        pitch='b',
                        octave=4,
                        duration=rest_dur + 'r',
                        start_time=prev_end,
                        original_frequency=None,
                        quantized_note='rest'
                    ))

            # Quantize pitch; use Viterbi duration
            detected_midi = frequency_to_midi(event.frequency)
            quantized_midi = find_nearest_allowed_note(detected_midi, self.allowed_midi)
            note_name, octave = midi_to_note_name(quantized_midi)
            duration = viterbi_durations[i]

            musical_notes.append(MusicalNote(
                pitch=note_name,
                octave=octave,
                duration=duration,
                start_time=event.start_time,
                original_frequency=event.frequency,
                quantized_note=f"{note_name}{octave}"
            ))

        musical_notes = self._apply_melodic_smoothing(musical_notes)
        return musical_notes

    def _apply_melodic_smoothing(
        self,
        notes: List[MusicalNote],
        max_jump_semitones: int = 12
    ) -> List[MusicalNote]:
        """
        Reduce excessive octave jumps between consecutive pitched notes.
        Rest notes are skipped for comparison purposes.
        """
        if len(notes) <= 1:
            return notes

        smoothed: List[MusicalNote] = [notes[0]]
        last_pitched_midi: int | None = None

        if notes[0].quantized_note != 'rest' and notes[0].original_frequency:
            last_pitched_midi = frequency_to_midi(notes[0].original_frequency)

        for note in notes[1:]:
            if note.quantized_note == 'rest':
                smoothed.append(note)
                continue

            curr_midi = frequency_to_midi(note.original_frequency)

            if last_pitched_midi is not None:
                interval = abs(curr_midi - last_pitched_midi)

                if interval > max_jump_semitones:
                    base_note = note.pitch
                    possible_midi = [
                        m for m in self.allowed_midi
                        if midi_to_note_name(m)[0] == base_note
                    ]

                    if possible_midi:
                        closest_midi = min(
                            possible_midi,
                            key=lambda m: abs(m - last_pitched_midi)
                        )
                        note_name, octave = midi_to_note_name(closest_midi)
                        note = MusicalNote(
                            pitch=note_name,
                            octave=octave,
                            duration=note.duration,
                            start_time=note.start_time,
                            original_frequency=note.original_frequency,
                            quantized_note=f"{note_name}{octave}"
                        )

            last_pitched_midi = frequency_to_midi(note.original_frequency)
            smoothed.append(note)

        return smoothed
