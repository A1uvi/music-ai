#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[start]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $1"; }
err()  { echo -e "${RED}[error]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[info]${NC}  $1"; }

# ── Checks ────────────────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || err "python3 not found. Install Python 3.11+."
command -v ffmpeg  >/dev/null 2>&1 || err "ffmpeg not found. Run: brew install ffmpeg"
command -v node    >/dev/null 2>&1 || err "node not found. Install Node.js 18+."
command -v npm     >/dev/null 2>&1 || err "npm not found. Install Node.js 18+."

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
NODE_VERSION=$(node --version)
log "Python $PYTHON_VERSION detected"
log "Node $NODE_VERSION detected"

# ── Virtual environment ───────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ── Backend dependencies ──────────────────────────────────────────────────────
log "Installing backend dependencies..."
pip install --quiet --upgrade pip
pip install --quiet \
  "pydantic-settings" \
  "setuptools>=65"
pip install --quiet -r "$BACKEND_DIR/requirements.txt"

# Upgrade librosa if version is < 0.11 (0.10.x has a pkg_resources issue on Python 3.12)
LIBROSA_VERSION=$(python3 -c "import librosa; print(librosa.__version__)" 2>/dev/null || echo "0.0.0")
LIBROSA_MAJOR=$(echo "$LIBROSA_VERSION" | cut -d. -f1)
LIBROSA_MINOR=$(echo "$LIBROSA_VERSION" | cut -d. -f2)
if [ "$LIBROSA_MAJOR" -eq 0 ] && [ "$LIBROSA_MINOR" -lt 11 ]; then
  warn "librosa $LIBROSA_VERSION detected — upgrading to 0.11+ for Python 3.12 compatibility..."
  pip install --quiet --upgrade librosa
fi

log "Backend dependencies ready"

# ── Frontend dependencies ─────────────────────────────────────────────────────
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  log "Installing frontend dependencies..."
  npm install --prefix "$FRONTEND_DIR" --silent
fi

log "Frontend dependencies ready"

# ── Free ports ────────────────────────────────────────────────────────────────
for PORT in 8000 3000; do
  if lsof -ti:$PORT >/dev/null 2>&1; then
    warn "Port $PORT in use — stopping existing process..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
done

# ── Cleanup on exit ───────────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  log "Shutting down..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait
  log "Done."
}
trap cleanup INT TERM

# ── Start backend ─────────────────────────────────────────────────────────────
log "Starting backend  → http://localhost:8000"
cd "$BACKEND_DIR"
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# ── Start frontend ────────────────────────────────────────────────────────────
log "Starting frontend → http://localhost:3000"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

info "Both services running. Press Ctrl+C to stop."
echo ""

wait
