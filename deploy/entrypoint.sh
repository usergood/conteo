#!/bin/sh
# Starts FastAPI on the internal port, then the Next.js standalone server.
set -e

mkdir -p "$DATA_DIR"

cd /app/backend
/app/venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001 &
API_PID=$!

trap 'kill $API_PID 2>/dev/null || true' EXIT INT TERM

cd /app/frontend
exec node server.js