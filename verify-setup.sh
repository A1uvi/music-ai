#!/bin/bash

# Verification script for Music Transcription project setup

echo "🎵 Music Transcription Project - Setup Verification"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        return 1
    fi
}

echo "📁 Project Structure:"
check_dir "backend"
check_dir "frontend"
check_dir "backend/app"
check_dir "frontend/src"
echo ""

echo "🐍 Backend Critical Files:"
check_file "backend/requirements.txt"
check_file "backend/Dockerfile"
check_file "backend/app/main.py"
check_file "backend/app/config.py"
check_file "backend/app/services/pitch_detector.py"
check_file "backend/app/services/note_quantizer.py"
check_file "backend/app/services/audio_extractor.py"
check_file "backend/app/services/notation_generator.py"
check_file "backend/app/api/routes/transcription.py"
echo ""

echo "⚛️  Frontend Critical Files:"
check_file "frontend/package.json"
check_file "frontend/next.config.js"
check_file "frontend/tailwind.config.js"
check_file "frontend/tsconfig.json"
check_file "frontend/src/app/page.tsx"
check_file "frontend/src/app/layout.tsx"
check_file "frontend/src/hooks/useTranscription.ts"
check_file "frontend/src/hooks/useSSE.ts"
check_file "frontend/src/components/display/SheetMusicViewer.tsx"
echo ""

echo "📄 Documentation Files:"
check_file "README.md"
check_file "QUICKSTART.md"
check_file "IMPLEMENTATION_SUMMARY.md"
check_file "docker-compose.yml"
check_file ".env.example"
echo ""

echo "🔧 System Requirements:"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Python 3 not found in PATH"
fi

# Check Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js: $NODE_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Node.js not found in PATH"
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker: $DOCKER_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Docker not found in PATH"
fi

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1)
    echo -e "${GREEN}✓${NC} FFmpeg: $FFMPEG_VERSION"
else
    echo -e "${YELLOW}⚠${NC} FFmpeg not found (required for audio processing)"
    echo "   Install: brew install ffmpeg"
fi

echo ""
echo "📊 File Statistics:"
PY_COUNT=$(find backend -name "*.py" 2>/dev/null | wc -l | xargs)
TS_COUNT=$(find frontend/src -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l | xargs)
echo "   Python files: $PY_COUNT"
echo "   TypeScript files: $TS_COUNT"
echo ""

echo "🚀 Next Steps:"
echo "   1. Review QUICKSTART.md for setup instructions"
echo "   2. Copy .env.example to .env if needed"
echo "   3. Choose Docker or manual setup"
echo "   4. Start the application and test"
echo ""
echo "✨ Setup verification complete!"
