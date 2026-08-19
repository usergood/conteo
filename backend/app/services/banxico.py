"""Banxico DOF exchange rate service (ticket 02).

Fetches the official FIX rate (USD/MXN) from Banxico's SIE API Rest
(series SF43718). Caches for 24h. Falls back to manual entry with
±5% validation when API is unavailable.

Banxico publishes at ~10:00 CDMX; invoices after that use same-day rate.
Weekends/holidays use the last published rate.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx

# SIE API series for USD/MXN FIX (DOF)
BANXICO_SERIES = "SF43718"
BANXICO_URL = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{BANXICO_SERIES}/datos"

CACHE_TTL_HOURS = 24
STALE_TTL_HOURS = 48


class BanxicoError(Exception):
    pass


def fetch_banxico_rate(api_key: str | None = None) -> Decimal | None:
    """Fetch the latest USD/MXN FIX rate from Banxico.

    Returns None if the API is unreachable or returns no data.
    Requires a BANXICO_API_KEY env var or the passed api_key.
    """
    if api_key is None:
        return None

    headers = {"Bmx-Token": api_key}
    try:
        resp = httpx.get(
            BANXICO_URL,
            headers=headers,
            params={"tipo": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        series = data.get("bmx", {}).get("series", [])
        if not series:
            return None
        datos = series[0].get("datos", [])
        if not datos:
            return None
        # Most recent datum
        latest = datos[-1]
        valor = latest.get("dato")
        if valor is None:
            return None
        return Decimal(valor)
    except Exception:
        return None


def get_cached_rate(conn: sqlite3.Connection) -> dict | None:
    """Return the cached Banxico rate if still fresh."""
    row = conn.execute(
        "SELECT * FROM fx_snapshots WHERE base = 'BANXICO_DOF' ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    age = datetime.now(timezone.utc) - fetched
    if age > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return {"rate": Decimal(row["rates_json"]), "fetched_at": row["fetched_at"]}


def cache_rate(conn: sqlite3.Connection, rate: Decimal) -> None:
    """Store the fetched rate in the cache."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO fx_snapshots (base, rates_json, fetched_at, source, stale) "
        "VALUES (?, ?, ?, ?, ?)",
        ("BANXICO_DOF", str(rate), now, "banxico", 0),
    )
    conn.commit()


def validate_manual_rate(
    proposed: Decimal,
    last_known: Decimal | None,
    tolerance_pct: float = 5.0,
) -> bool:
    """Validate a manually-entered rate against the last known rate.

    Returns True if the proposed rate is within ±tolerance_pct of last_known,
    or if there is no last_known rate to compare against.
    """
    if last_known is None or last_known <= 0:
        return True
    diff_pct = abs(float(proposed - last_known) / float(last_known)) * 100
    return diff_pct <= tolerance_pct
