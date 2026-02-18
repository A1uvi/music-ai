# Developer Notes

## Implementation Details

### Critical Design Decisions

#### 1. Pitch Detection Algorithm
**Choice**: librosa's pYIN (probabilistic YIN) algorithm

**Rationale**:
- More robust than autocorrelation for real music
- Provides confidence scores to filter poor detections
- Handles vibrato and pitch variations well
- Industry standard for melody extraction

**Parameters**:
- `fmin=65 Hz (C2)`, `fmax=2093 Hz (C7)` - Vocal/instrumental range
- Confidence threshold: 0.5 minimum
- Harmonic separation before pitch detection reduces noise

#### 2. Note Quantization Strategy
**Nearest-neighbor mapping** with melodic smoothing

**Why not just round to nearest note?**
- Raw rounding creates excessive octave jumps
- Melodic smoothing preserves musical coherence
- Maximum 12-semitone jump constraint
- Prefers closest octave when multiple options exist

**Example**:
```
Detected: C4 → D5 (huge jump)
Smoothed: C4 → D4 (same octave, musically sensible)
```

#### 3. Server-Sent Events vs WebSocket
**Choice**: SSE for progress updates

**Rationale**:
- Simpler than WebSocket for one-way communication
- Native browser EventSource API
- Automatic reconnection
- Works through HTTP/HTTPS proxies
- No need for bidirectional communication

**Alternative considered**: Polling (rejected - inefficient, higher latency)

#### 4. Background Task Processing
**Choice**: asyncio.create_task() for background jobs

**Rationale**:
- Simple for MVP without external dependencies
- Works well for 1-2 minute processing times
- No need for Celery/Redis complexity yet

**Production consideration**: For scale, migrate to Celery + Redis queue

#### 5. VexFlow Client-Side Rendering
**Choice**: Client-side rendering in browser

**Rationale**:
- Interactive features possible (future: playback sync)
- No server-side rendering complexity
- Reduces backend load
- Users can export/print directly

**Trade-off**: Initial load includes VexFlow library (~500KB)

### Code Organization Principles

#### Backend Structure
```
services/     # Business logic (pure functions where possible)
api/routes/   # HTTP endpoint handlers (thin controllers)
models/       # Data structures (Pydantic models)
utils/        # Shared utilities (music theory, progress tracking)
core/         # Framework-level code (exceptions, logging)
```

**Pattern**: Fat services, thin controllers
- API routes delegate to services
- Services are testable without HTTP context
- Models enforce validation at boundaries

#### Frontend Structure
```
components/ui/       # Base design system components
components/forms/    # Composed form widgets
components/display/  # Data presentation components
components/layout/   # Structural components
hooks/              # Reusable React logic
lib/                # Pure utility functions
types/              # TypeScript interfaces
```

**Pattern**: Container/Presentational split
- Hooks manage state and side effects
- Components focus on rendering
- Types shared across layers

### Performance Considerations

#### Backend
1. **Audio Processing**
   - Runs in executor (thread pool) to avoid blocking
   - File cleanup after processing
   - Temporary file TTL prevents disk bloat

2. **Memory Management**
   - Audio loaded at 22050 Hz (not 44100) reduces memory 2x
   - Harmonic separation only for melody, discards percussive
   - Job results held in memory for 1 hour, then cleaned

3. **Scaling Bottlenecks**
   - CPU-bound: pitch detection (~60s for 3min song)
   - I/O-bound: YouTube download (depends on network)
   - **Solution for scale**: Horizontal scaling with job queue

#### Frontend
1. **Bundle Size**
   - VexFlow dynamically imported (code splitting)
   - Tailwind purges unused CSS
   - Next.js automatic optimization

2. **SSE Connection**
   - Auto-reconnect on disconnect
   - Keepalive messages every 30s
   - Clean disconnection on completion

### Testing Strategy

#### Backend Tests (To Implement)
```python
# Unit tests
test_pitch_detector.py     # Mock audio files, verify detection
test_note_quantizer.py     # Known pitches → expected notes
test_music_theory.py       # Frequency conversions

# Integration tests
test_api.py               # Full pipeline with sample audio
```

#### Frontend Tests (To Implement)
```typescript
// Component tests (React Testing Library)
Button.test.tsx           // Interactions, loading states
SheetMusicViewer.test.tsx // VexFlow rendering

// Hook tests
useTranscription.test.ts  // State transitions, SSE events

// E2E tests (Playwright)
transcription.spec.ts     // Full user flow
```

### Security Considerations

1. **File Upload Validation**
   - Size limit: 100MB
   - Type whitelist: audio/video only
   - No executable extensions allowed

2. **URL Validation**
   - Only YouTube/YouTube Music domains
   - yt-dlp sandboxing prevents arbitrary code

3. **Input Sanitization**
   - Pydantic validates all API inputs
   - Note names validated against whitelist
   - No SQL injection risk (no database)

4. **CORS Configuration**
   - Whitelist specific frontend origins
   - No credentials in CORS (stateless)

### Known Edge Cases

1. **Very short audio (< 1 second)**
   - May not detect any pitches
   - Returns empty result with warning

2. **Polyphonic music (chords)**
   - Extracts only dominant pitch
   - May "jump" between chord notes

3. **Heavy percussion**
   - HPSS separation helps but not perfect
   - Drum-heavy tracks may have poor accuracy

4. **Vibrato and glissando**
   - pYIN handles vibrato reasonably
   - Glissando may create note "stuttering"

5. **Very high/low frequencies**
   - Outside C2-C7 range ignored
   - Bass instruments may lose octave information

### Future Optimization Opportunities

1. **Caching**
   - Cache YouTube downloads by video ID
   - Cache pitch detection results
   - Estimated 80% hit rate for popular songs

2. **Parallel Processing**
   - Split audio into chunks
   - Process chunks in parallel
   - Merge results
   - **Speedup**: 2-4x on multi-core systems

3. **Model Improvements**
   - Train custom melody extraction model
   - Use Demucs for better source separation
   - Implement chord detection

4. **Client-Side Processing**
   - WebAssembly version of pitch detection
   - Process in browser for short clips
   - Reduces server load

### Debugging Tips

#### Backend
```bash
# Enable debug logging
DEBUG=true uvicorn app.main:app --reload

# Test pitch detection directly
python -c "
from app.services.pitch_detector import PitchDetector
import asyncio
detector = PitchDetector()
result = asyncio.run(detector.detect_pitches('test.wav'))
print(result)
"

# Monitor SSE events
curl -N http://localhost:8000/api/py/transcribe/status/{job_id}
```

#### Frontend
```javascript
// Log SSE events in browser console
// Already implemented in useSSE hook

// Inspect VexFlow rendering
// Check containerRef in SheetMusicViewer component

// Debug state transitions
// Add console.log in useTranscription hook
```

### Dependencies Explained

#### Backend
- `librosa` - Audio analysis (pitch detection, onset detection)
- `soundfile` - Audio I/O (WAV reading)
- `numpy` - Array operations for audio signals
- `scipy` - Signal processing utilities
- `yt-dlp` - YouTube audio extraction
- `ffmpeg-python` - Audio format conversion
- `pydantic` - Data validation
- `fastapi` - Web framework

#### Frontend
- `vexflow` - Music notation rendering
- `axios` - HTTP client (better error handling than fetch)
- `zod` - Runtime validation (currently unused, reserved)
- `clsx` - CSS class merging utility

### Environment Variables

```bash
# Backend (.env)
DEBUG=true                    # Enable debug logging
CORS_ORIGINS=http://localhost:3000  # Allowed frontend origins
TEMP_DIR=/tmp/audio          # Temporary file storage
MAX_FILE_SIZE=104857600      # 100MB in bytes
SAMPLE_RATE=22050            # Audio sample rate
HOP_LENGTH=512               # Frame hop for analysis
JOB_TIMEOUT=600              # Max processing time (seconds)

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

### Common Development Issues

**Issue**: `ModuleNotFoundError: No module named 'librosa'`
**Solution**: Activate virtual environment, `pip install -r requirements.txt`

**Issue**: `RuntimeError: No FFmpeg found`
**Solution**: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

**Issue**: Sheet music not rendering
**Solution**: Check browser console for VexFlow errors, ensure dynamic import succeeded

**Issue**: SSE connection drops immediately
**Solution**: Check CORS settings, verify backend running on correct port

**Issue**: Processing hangs at "analyzing"
**Solution**: Check backend logs, may be out of memory (reduce audio file size)

### Production Checklist

- [ ] Set DEBUG=false
- [ ] Configure proper CORS origins
- [ ] Set up error tracking (Sentry)
- [ ] Configure logging aggregation
- [ ] Add rate limiting on API endpoints
- [ ] Set up CDN for frontend assets
- [ ] Configure file storage with TTL
- [ ] Add monitoring/alerting
- [ ] Load test with concurrent users
- [ ] Set up CI/CD pipeline
- [ ] Add database for job persistence (optional)
- [ ] Configure backup strategy for results

### Useful Commands

```bash
# Backend
cd backend
python -m pytest tests/                    # Run tests
uvicorn app.main:app --reload --port 8000 # Dev server
python -m black app/                       # Format code
python -m pylint app/                      # Lint code

# Frontend
cd frontend
npm test                                   # Run tests
npm run dev                                # Dev server
npm run build                              # Production build
npm run lint                               # Lint code

# Docker
docker-compose up --build                  # Build and start
docker-compose down -v                     # Stop and remove volumes
docker-compose logs -f backend             # Follow backend logs
docker-compose exec backend bash           # Shell into backend
```

---

**Last Updated**: 2026-02-16
**Version**: 1.0.0
**Maintainer**: Development Team
