"""Single source of version truth for the backend (ticket: version in UI).

Reads the root `VERSION` file. In dev the file is at the repo root (this module
is `backend/app/services/version.py` → three levels up); in the container it is
copied to `/app/VERSION` by the Dockerfile. An `APP_VERSION` env var overrides
both (not used in normal operation)."""
import os
from pathlib import Path


def current_version() -> str:
    override = os.environ.get("APP_VERSION", "").strip()
    if override:
        return override
    candidates = (
        Path(__file__).resolve().parents[3] / "VERSION",  # repo root (dev)
        Path("/app/VERSION"),  # container runtime
    )
    for path in candidates:
        try:
            value = path.read_text().strip()
        except OSError:
            continue
        if value:
            return value
    return "0.0.0"
