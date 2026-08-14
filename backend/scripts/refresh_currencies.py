#!/usr/bin/env python3
"""Regenerate the canonical currency list from the FX provider (release ritual).

Fetches the provider's current `latest/USD` rates keys, keeps the existing
committed names from backend/app/currencies.json for codes already present, and
writes a new list. Any code that is new (or whose name was previously left
blank) is emitted with an empty name and reported on stderr — the human must
fill these in against ISO 4217 before releasing (see RELEASING.md).

Usage (from the repo root):
    python backend/scripts/refresh_currencies.py

Exits 0 on success even when new codes need names (it still writes the file);
exits 1 if the provider is unreachable or returned no rates.
"""

import json
import sys
from pathlib import Path

import httpx

PROVIDER_URL = "https://open.er-api.com/v6/latest/USD"
LIST_PATH = Path(__file__).resolve().parents[1] / "app" / "currencies.json"


def main() -> int:
    try:
        resp = httpx.get(PROVIDER_URL, timeout=30)
        resp.raise_for_status()
        rates = resp.json().get("rates")
    except httpx.HTTPError as exc:
        print(f"error: could not reach provider: {exc}", file=sys.stderr)
        return 1
    if not isinstance(rates, dict) or not rates:
        print("error: provider returned no rates", file=sys.stderr)
        return 1

    existing = {}
    if LIST_PATH.exists():
        existing = {e["code"]: e["name"] for e in json.loads(LIST_PATH.read_text(encoding="utf-8"))}

    codes = sorted(rates.keys())
    entries = [{"code": code, "name": existing.get(code, "")} for code in codes]

    new_codes = [e["code"] for e in entries if not e["name"]]
    LIST_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} currencies to {LIST_PATH}")

    if new_codes:
        print(
            "warning: these codes need ISO 4217 names filled in manually:\n  "
            + "\n  ".join(new_codes),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
