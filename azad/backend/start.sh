#!/bin/bash
# Restart the Azad MIS backend (FLP-only deployment).
# Loads env from .env, kills any prior uvicorn on port 8080, then relaunches.

cd "$(dirname "$0")"

# Source .env if present (lines like KEY=VALUE)
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

# Stop any prior instance on the same port
pkill -f "uvicorn main:app.*8080" 2>/dev/null
sleep 1

mkdir -p "${UPLOAD_DIR:-./uploads}"

# Activate venv if it exists, otherwise use system python
if [ -f venv/bin/activate ]; then
  . venv/bin/activate
fi

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 > /tmp/azad-mis-backend.log 2>&1 &
echo $! > /tmp/azad-mis-backend.pid
sleep 3

# Quick health probe
curl -s --max-time 5 http://localhost:8080/api/health || echo "(backend still warming up)"
echo
