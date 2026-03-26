#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  start.sh  –  Start backend + frontend in one command
#  Usage:  ./start.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── Colours ──────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

log()  { echo -e "${CYAN}[start.sh]${RESET} $*"; }
ok()   { echo -e "${GREEN}[start.sh]${RESET} $*"; }
warn() { echo -e "${YELLOW}[start.sh]${RESET} $*"; }

# ── Cleanup: kill both child processes on exit / Ctrl+C ──────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  warn "Shutting down…"
  [[ -n "$BACKEND_PID"  ]] && kill "$BACKEND_PID"  2>/dev/null || true
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  ok "Done. Goodbye!"
}
trap cleanup EXIT INT TERM

# ── Backend ──────────────────────────────────────────────────
log "Starting backend (FastAPI on :8000)…"

# Prefer the project-level venv, fall back to system python
if [[ -f "$BACKEND_DIR/.venv/bin/python" ]]; then
  PYTHON="$BACKEND_DIR/.venv/bin/python"
elif [[ -f "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
else
  PYTHON="python3"
  warn "No virtual-env found – using system python3"
fi

# Copy .env.example → .env if .env is missing
if [[ ! -f "$BACKEND_DIR/.env" && -f "$BACKEND_DIR/.env.example" ]]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  warn ".env not found – copied from .env.example (edit it if needed)"
fi

(
  cd "$BACKEND_DIR"
  "$PYTHON" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────
log "Starting frontend (Vite on :5173)…"

(
  cd "$FRONTEND_DIR"
  npm run dev -- --host
) &
FRONTEND_PID=$!

# ── Summary ──────────────────────────────────────────────────
ok "Both services started!"
echo -e "  ${GREEN}Backend${RESET}  → http://localhost:8000  (API docs: http://localhost:8000/docs)"
echo -e "  ${GREEN}Frontend${RESET} → http://localhost:5173"
echo -e "  Press ${YELLOW}Ctrl+C${RESET} to stop everything.\n"

# Wait for either process to exit
wait -n 2>/dev/null || wait
