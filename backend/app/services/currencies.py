"""Canonical currency list — single source of truth (ticket 14).

A frozen committed list of exactly the currencies the FX provider carries,
copied from the research deliverable (ticket 13). Regenerated on release, never
runtime-derived. Served via GET /api/currencies and enforced on write.
"""

import json
from pathlib import Path

_LIST_PATH = Path(__file__).resolve().parent.parent / "currencies.json"


def _load() -> dict[str, str]:
    data = json.loads(_LIST_PATH.read_text(encoding="utf-8"))
    return {entry["code"]: entry["name"] for entry in data}


CURRENCIES: dict[str, str] = _load()
CODES: set[str] = set(CURRENCIES)


def is_supported(code: str) -> bool:
    """True when `code` is one of the provider's currency codes (case-insensitive)."""
    return code.upper() in CODES
