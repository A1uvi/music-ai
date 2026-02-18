# Quick Start Guide

## Setup Instructions

### Option 1: Docker (Recommended)

1. **Install Docker Desktop**
   - macOS: Download from https://www.docker.com/products/docker-desktop
   - Ensure Docker is running

2. **Start the application**
```bash
cd /Users/alvianaqvi/vsc_code/music-ai
docker-compose up --build
```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup

1. **Install Python dependencies**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

2. **Install FFmpeg** (required for audio processing)
```bash
# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

3. **Run the backend server**
```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

1. **Install Node.js dependencies**
```bash
cd frontend

# Install packages
npm install
```

2. **Run the development server**
```bash
npm run dev
```

3. **Access the application**
   - Open http://localhost:3000 in your browser

## Testing the Application

### Test with URL

1. Open http://localhost:3000
2. Select "From URL"
3. Enter a YouTube URL (e.g., a short music video)
4. Select allowed notes (try "C Major" preset)
5. Click "Transcribe from URL"
6. Watch real-time progress updates
7. View the generated sheet music

### Test with File Upload

1. Select "Upload File"
2. Choose an audio file (MP3, WAV) or video file (MP4)
3. Select allowed notes
4. Click "Transcribe from File"
5. View results

## Project Structure

```
music-ai/
├── backend/           # Python FastAPI backend
│   ├── app/
│   │   ├── services/  # Audio processing logic
│   │   ├── api/       # API routes
│   │   ├── models/    # Data models
│   │   └── utils/     # Helper functions
│   └── requirements.txt
│
├── frontend/          # Next.js frontend
│   ├── src/
│   │   ├── app/       # Next.js pages
│   │   ├── components/# React components
│   │   ├── hooks/     # React hooks
│   │   └── lib/       # Utilities
│   └── package.json
│
└── docker-compose.yml # Docker configuration
```

## Common Issues

### Backend won't start
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check Python version: `python3 --version` (need 3.11+)
- Activate virtual environment: `source venv/bin/activate`

### Frontend won't start
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (need 20+)

### Processing fails
- Check file size (max 100MB)
- Ensure valid YouTube URL
- Check backend logs for errors

### Sheet music not rendering
- Clear browser cache
- Check browser console for errors
- Ensure VexFlow loaded correctly

## Development Tips

### Backend Development

- API documentation: http://localhost:8000/docs
- Test endpoints with Swagger UI
- Logs appear in terminal
- Hot reload enabled with `--reload`

### Frontend Development

- Hot reload enabled by default
- Check browser console for errors
- Use React DevTools for debugging
- Tailwind CSS IntelliSense recommended

## Next Steps

1. Try different scales (Pentatonic, Minor, etc.)
2. Upload various audio files
3. Experiment with note constraints
4. Review the generated sheet music accuracy
5. Check out the API documentation at http://localhost:8000/docs

## Getting Help

- Check README.md for detailed documentation
- Review the implementation plan in CLAUDE.md
- Open an issue on GitHub for bugs
- Review API responses in browser DevTools Network tab
