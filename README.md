# Music Transcription Website

Convert songs to sheet music with custom note constraints. Extract melodies from YouTube videos or audio files and generate professional notation using only your specified notes.

## Features

- **URL-based transcription**: Extract audio from YouTube and YouTube Music
- **File upload support**: Upload audio/video files (MP3, WAV, MP4)
- **Custom note constraints**: Specify exactly which notes can appear in the transcription
- **Real-time progress**: Live updates during processing with Server-Sent Events
- **Professional notation**: High-quality sheet music rendering with VexFlow
- **Common scale presets**: Quick selection for major, minor, and pentatonic scales
- **Responsive design**: Works seamlessly on desktop and mobile devices

## Tech Stack

### Frontend
- Next.js 15 with React 19
- TypeScript
- Tailwind CSS (8pt spacing system)
- VexFlow for sheet music rendering
- Server-Sent Events for real-time updates

### Backend
- Python FastAPI
- librosa for audio analysis and pitch detection
- yt-dlp for YouTube audio extraction
- NumPy and SciPy for signal processing

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Or manually: Node.js 20+, Python 3.11+, FFmpeg

### Quick Start with Docker

1. Clone the repository
```bash
git clone <repository-url>
cd music-ai
```

2. Copy environment file
```bash
cp .env.example .env
```

3. Start services
```bash
docker-compose up
```

4. Open browser to http://localhost:3000

### Manual Setup

#### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Ensure FFmpeg is installed
# macOS: brew install ffmpeg
# Ubuntu: apt-get install ffmpeg

# Run server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## How It Works

1. **Audio Extraction**: Downloads audio from URL or processes uploaded file
2. **Preprocessing**: Converts audio to WAV format, separates harmonic components
3. **Pitch Detection**: Uses librosa's pYIN algorithm to detect fundamental frequencies
4. **Onset Detection**: Identifies note boundaries using onset strength analysis
5. **Note Quantization**: Maps detected pitches to nearest allowed notes (any octave)
6. **Melodic Smoothing**: Reduces excessive octave jumps for musical coherence
7. **Duration Quantization**: Converts durations to standard musical values (1/4, 1/8, etc.)
8. **Notation Generation**: Creates VexFlow-compatible sheet music data
9. **Rendering**: Displays professional notation with clefs, key signatures, and measures

## API Endpoints

### POST /api/py/transcribe/url
Initiate transcription from URL
```json
{
  "url": "https://youtube.com/watch?v=...",
  "allowed_notes": ["C", "D", "E", "F", "G", "A", "B"],
  "source_type": "youtube"
}
```

### POST /api/py/transcribe/upload
Upload audio file for transcription
- `file`: Audio/video file (max 100MB)
- `allowed_notes`: JSON array of note names

### GET /api/py/transcribe/status/{job_id}
Server-Sent Events endpoint for real-time progress updates

### GET /api/py/transcribe/result/{job_id}
Retrieve completed transcription result

## Design System

This project follows strict design principles:

- **Spacing**: 8pt grid system (8px, 16px, 24px, 32px, 48px, 64px)
- **Typography**: Inter font family with consistent type ramp
- **Colors**: Disciplined palette with high contrast for readability
- **Components**: Consistent border radius (8px), shadows, and transitions
- **Interactions**: Subtle, purposeful animations with proper loading states
- **Layout**: Proper grid alignment and predictable spacing

## Configuration

Key settings in `.env`:

- `MAX_FILE_SIZE`: Maximum upload size in bytes (default 100MB)
- `SAMPLE_RATE`: Audio sample rate for processing (default 22050 Hz)
- `JOB_TIMEOUT`: Maximum processing time in seconds (default 600)
- `CORS_ORIGINS`: Allowed frontend origins

## Known Limitations

- **Monophonic only**: Currently extracts single melodic line (no chords)
- **YouTube only**: Spotify/Apple Music not yet supported
- **No manual editing**: Detected notes cannot be corrected in UI
- **Processing time**: Complex songs may take 1-2 minutes

## Future Enhancements

- Multi-voice/harmony detection
- Audio playback synced with sheet music highlighting
- Manual note correction interface
- Export to MusicXML, MIDI, PDF
- Real-time transcription from microphone
- AI-improved pitch detection models
- Collaboration and sharing features

## License

MIT

## Contributing

Contributions welcome. Please ensure all code follows the established design system principles.
