from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    app_name: str = "Music Transcription API"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # File Settings
    temp_dir: Path = Path("/tmp/audio")
    max_file_size: int = 104857600  # 100MB

    # Audio Processing Settings
    sample_rate: int = 44100   # doubles frequency resolution for beat tracking
    hop_length: int = 128      # finer time grid

    # Job Settings
    job_timeout: int = 600  # 10 minutes

    # Phase 2a: Noise reduction (noisereduce) — enabled by default when available
    enable_preprocessing: bool = True

    # Phase 2b: Melody source separation (demucs) — opt-in; model is ~700 MB
    # and significantly slower on CPU. Can be overridden per-request via the
    # enable_source_separation field in TranscribeUrlRequest.
    enable_source_separation: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure temp directory exists
settings.temp_dir.mkdir(parents=True, exist_ok=True)
