class AudioExtractionError(Exception):
    """Raised when audio extraction from URL fails."""
    pass


class PitchDetectionError(Exception):
    """Raised when pitch detection fails."""
    pass


class InvalidInputError(Exception):
    """Raised when user input validation fails."""
    pass


class JobNotFoundError(Exception):
    """Raised when requested job ID doesn't exist."""
    pass


class ProcessingTimeoutError(Exception):
    """Raised when processing exceeds time limit."""
    pass
