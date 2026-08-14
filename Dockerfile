# syntax=docker/dockerfile:1
# Single container (ticket 07): Next.js standalone on :3000, FastAPI on an
# internal port, /api/* rewritten to it. DB + config in /data (mounted).

# ---------- 1. Build the Next.js standalone bundle ----------
FROM node:22-alpine AS web-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---------- 2. Runtime: Node (Next standalone) + Python (FastAPI) ----------
FROM node:22-bookworm-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    API_URL=http://127.0.0.1:8001

# Python + WeasyPrint system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    libffi8 libcairo2 libgdk-pixbuf-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN python -m venv /app/venv && /app/venv/bin/pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/

# Next standalone bundle: server.js + .next/static + public/ (logo, favicon)
COPY --from=web-build /build/.next/standalone/ ./frontend/
COPY --from=web-build /build/.next/static/ ./frontend/.next/static/
COPY --from=web-build /build/public ./frontend/public/

COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3000
VOLUME ["/data"]
ENTRYPOINT ["/entrypoint.sh"]