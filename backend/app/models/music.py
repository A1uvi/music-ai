from typing import List, Optional
from dataclasses import dataclass


@dataclass
class PitchEvent:
    """Represents a detected pitch with timing information."""
    frequency: float
    start_time: float
    duration: float
    confidence: float


@dataclass
class MusicalNote:
    """Represents a quantized musical note."""
    pitch: str  # Note name (C, D#, etc.)
    octave: int
    duration: str  # Musical duration (1/4, 1/8, etc.)
    start_time: float
    original_frequency: Optional[float] = None
    quantized_note: Optional[str] = None
