from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List


class SourceType(str, Enum):
    """Supported audio source types."""
    YOUTUBE = "youtube"
    YOUTUBE_MUSIC = "youtube_music"
    FILE_UPLOAD = "file_upload"


class TranscribeUrlRequest(BaseModel):
    """Request model for URL-based transcription."""
    url: str = Field(..., description="URL to YouTube or music platform")
    source_type: SourceType = Field(
        default=SourceType.YOUTUBE,
        description="Type of source platform"
    )
    allowed_notes: Optional[List[str]] = Field(
        default=None,
        description="Restrict output notes to this set (e.g. C-major scale). "
                    "If null, all 12 chromatic notes are allowed."
    )
    enable_source_separation: bool = Field(
        default=False,
        description="Run demucs melody separation before pitch detection (slower, more accurate)"
    )
