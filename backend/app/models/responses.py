from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class JobStatus(str, Enum):
    """Transcription job status."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    SEPARATING = "separating"      # Phase 2b: demucs source separation
    PREPROCESSING = "preprocessing"
    ANALYZING = "analyzing"
    QUANTIZING = "quantizing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscribeResponse(BaseModel):
    """Response for transcription initiation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    sse_endpoint: str = Field(..., description="Server-sent events endpoint for progress")


class NoteData(BaseModel):
    """Individual note in the transcription result."""
    pitch: str = Field(..., description="Note name (C, D#, etc.)")
    octave: int = Field(..., description="Octave number")
    duration: str = Field(..., description="Musical duration (q, 8, etc.)")
    start_time: float = Field(..., description="Start time in seconds")
    original_frequency: Optional[float] = Field(None, description="Original detected frequency")
    quantized_note: Optional[str] = Field(None, description="Quantized note name with octave")


class MusicMetadata(BaseModel):
    """Metadata about the transcribed music."""
    tempo: int = Field(default=120, description="Tempo in BPM")
    time_signature: str = Field(default="4/4", description="Time signature")
    key_signature: str = Field(default="C", description="Detected key signature")
    total_duration: float = Field(..., description="Total duration in seconds")
    note_count: int = Field(..., description="Number of notes detected")


class VexFlowMeasure(BaseModel):
    """A single measure in VexFlow format."""
    notes: List[Dict[str, Any]] = Field(..., description="Notes in this measure")
    time_signature: Optional[str] = Field(None, description="Time signature if changed")


class VexFlowData(BaseModel):
    """Sheet music data in VexFlow format."""
    measures: List[VexFlowMeasure] = Field(..., description="List of measures")
    clef: str = Field(default="treble", description="Musical clef")
    key: str = Field(default="C", description="Key signature")


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    notes: List[NoteData] = Field(..., description="List of transcribed notes")
    metadata: MusicMetadata = Field(..., description="Music metadata")


class TranscriptionJobResult(BaseModel):
    """Full job result with VexFlow data."""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    result: Optional[TranscriptionResult] = Field(None, description="Transcription result")
    vexflow_data: Optional[VexFlowData] = Field(None, description="VexFlow rendering data")
    error: Optional[str] = Field(None, description="Error message if failed")


class ProgressEvent(BaseModel):
    """Progress update event."""
    stage: str = Field(..., description="Current processing stage")
    percent: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Human-readable progress message")
