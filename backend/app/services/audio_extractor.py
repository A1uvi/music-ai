import yt_dlp
from pathlib import Path
from typing import Optional
import asyncio
from ..core.exceptions import AudioExtractionError


class AudioExtractor:
    """
    Extracts audio from YouTube and other video platforms using yt-dlp.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize audio extractor.

        Args:
            output_dir: Directory to save extracted audio files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def extract_from_url(
        self,
        url: str,
        job_id: str
    ) -> Path:
        """
        Extract audio from a URL.

        Args:
            url: Video URL (YouTube, YouTube Music, etc.)
            job_id: Unique job identifier for filename

        Returns:
            Path to extracted audio file

        Raises:
            AudioExtractionError: If extraction fails
        """
        output_path = self.output_dir / f"{job_id}.wav"

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': str(self.output_dir / f"{job_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
        }

        try:
            # Run yt-dlp in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._download_audio,
                url,
                ydl_opts
            )

            if not output_path.exists():
                raise AudioExtractionError(f"Audio file not created: {output_path}")

            return output_path

        except Exception as e:
            raise AudioExtractionError(f"Failed to extract audio: {str(e)}")

    def _download_audio(self, url: str, options: dict) -> None:
        """
        Internal method to download audio (runs in thread pool).

        Args:
            url: Video URL
            options: yt-dlp options

        Raises:
            Exception: If download fails
        """
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
