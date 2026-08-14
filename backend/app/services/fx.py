"""Live FX — open.er-api.com hourly poll, Frankfurter fallback, cached snapshot
(ticket 08). One snapshot keyed by base USD; other pairs cross-derived.

Refresh order: open.er-api.com → api.frankfurter.dev → keep the last cached
snapshot (marked stale). A snapshot older than 48h is treated as unusable by
callers (ticket 04: "no recent rate → render that source in its own currency,
exclude from MXN totals").
"""

import json
import logging
from datetime import datetime, timezone

import httpx

from .months import now_iso

log = logging.getLogger(__name__)

ER_API = "https://open.er-api.com/v6/latest/USD"
FRANKFURTER = "https://api.frankfurter.dev/v2/rates?base=USD&quotes=MXN,SEK"

STALE_HOURS = 48  # beyond this a cached snapshot is unusable for totals


def _parse_er_api(payload: dict) -> dict | None:
    rates = payload.get("rates")
    if not isinstance(rates, dict) or "MXN" not in rates:
        return None
    return {
        "rates": {k: float(v) for k, v in rates.items()},
        "fetched_at": now_iso(),
        "source": "er-api",
    }


def _parse_frankfurter(payload: dict) -> dict | None:
    rates = payload.get("rates")
    if not isinstance(rates, dict) or "MXN" not in rates:
        return None
    return {
        "rates": {k: float(v) for k, v in rates.items()},
        "fetched_at": now_iso(),
        "source": "frankfurter",
    }


async def fetch_from_providers() -> dict | None:
    """Try er-api then Frankfurter. Returns a snapshot dict or None."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(ER_API)
            resp.raise_for_status()
            snap = _parse_er_api(resp.json())
            if snap:
                return snap
        except httpx.HTTPError as exc:
            log.warning("er-api failed: %s", exc)
        try:
            resp = await client.get(FRANKFURTER)
            resp.raise_for_status()
            snap = _parse_frankfurter(resp.json())
            if snap:
                return snap
        except httpx.HTTPError as exc:
            log.warning("frankfurter failed: %s", exc)
    return None


def save_snapshot(conn, snapshot: dict, stale: bool = False) -> None:
    conn.execute(
        "INSERT INTO fx_snapshots (base, rates_json, fetched_at, source, stale) "
        "VALUES ('USD', ?, ?, ?, ?) "
        "ON CONFLICT(base) DO UPDATE SET rates_json=excluded.rates_json, "
        "fetched_at=excluded.fetched_at, source=excluded.source, stale=excluded.stale",
        (json.dumps(snapshot["rates"]), snapshot["fetched_at"], snapshot["source"], int(stale)),
    )
    conn.commit()


async def refresh_snapshot(conn) -> dict:
    """Poll providers; on total failure keep the cached snapshot (stale)."""
    existing = current_snapshot(conn)
    snap = await fetch_from_providers()
    if snap:
        save_snapshot(conn, snap, stale=False)
        return snap
    if existing:
        save_snapshot(conn, existing, stale=True)
        return {**existing, "stale": True}
    return {"rates": {}, "fetched_at": now_iso(), "source": "cached", "stale": True}


def current_snapshot(conn) -> dict | None:
    row = conn.execute(
        "SELECT rates_json, fetched_at, source, stale FROM fx_snapshots WHERE base = 'USD'"
    ).fetchone()
    if row is None:
        return None
    return {
        "rates": json.loads(row["rates_json"]),
        "fetched_at": row["fetched_at"],
        "source": row["source"],
        "stale": bool(row["stale"]),
    }


def is_stale(snapshot: dict | None) -> bool:
    if snapshot is None:
        return True
    fetched = datetime.fromisoformat(snapshot["fetched_at"])
    age = datetime.now(timezone.utc) - fetched
    return age.total_seconds() > STALE_HOURS * 3600


def mxn_per(conn, currency: str) -> tuple[float | None, bool]:
    """MXN per 1 `currency` via cross-derivation from the USD snapshot.

    Returns (rate, stale_or_missing) — rate is None when the pair is unknown
    or the snapshot is unusably old.
    """
    snap = current_snapshot(conn)
    if is_stale(snap):
        return None, True
    rates = snap["rates"]
    usd_per_cur = rates.get(currency)
    usd_per_mxn = rates.get("MXN")
    if not usd_per_cur or not usd_per_mxn:
        return None, True
    return usd_per_mxn / usd_per_cur, bool(snap["stale"])
