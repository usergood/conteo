"""Calendar/month helpers shared by close, forecast, months and slips."""

import re
import sqlite3
from datetime import date, datetime, timezone, timedelta

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def month_key(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def current_month_key() -> str:
    today = date.today()
    return month_key(today.year, today.month)


def add_months(key: str, n: int) -> str:
    year, month = (int(p) for p in key.split("-"))
    idx = year * 12 + (month - 1) + n
    return month_key(idx // 12, idx % 12 + 1)


def month_bounds(key: str) -> tuple[str, str]:
    """(first day, last day) of the month, ISO."""
    year, month = (int(p) for p in key.split("-"))
    first = date(year, month, 1)
    last = first + timedelta(days=32)
    last = last.replace(day=1) - timedelta(days=1)
    return first.isoformat(), last.isoformat()


def commission_of(source_row: sqlite3.Row, project_row: sqlite3.Row) -> float:
    mode = source_row["commission_mode"]
    value = source_row["commission_value"]
    if mode == "pct":
        return project_row["value"] * value / 100
    if mode == "flat":
        return value
    return 0.0


def source_active_in(created_at_iso: str, month_key_str: str) -> bool:
    """A source's months begin the month it was added; no backfill (ticket 02)."""
    _, end = month_bounds(month_key_str)
    return created_at_iso[:10] <= end


def fully_closed_months(conn: sqlite3.Connection, owner_user_id: str) -> list[str]:
    """Every month in which every source that existed then is settled."""
    settlements = conn.execute(
        "SELECT month FROM settlements WHERE owner_user_id = ?", (owner_user_id,)
    ).fetchall()
    candidates = sorted({row["month"] for row in settlements})
    closed = []
    for month in candidates:
        if owner_month_fully_closed(conn, owner_user_id, month):
            closed.append(month)
    return closed


def owner_month_fully_closed(conn: sqlite3.Connection, owner_user_id: str, month: str) -> bool:
    """True when every source the owner had active that month is settled for it."""
    if not MONTH_RE.match(month):
        return False
    sources = conn.execute(
        "SELECT id, created_at, active FROM income_sources WHERE owner_user_id = ?",
        (owner_user_id,),
    ).fetchall()
    required = [
        s["id"] for s in sources if s["active"] and source_active_in(s["created_at"], month)
    ]
    if not required:
        return False
    settled = conn.execute(
        "SELECT source_id FROM settlements WHERE owner_user_id = ? AND month = ?",
        (owner_user_id, month),
    ).fetchall()
    settled_ids = {row["source_id"] for row in settled}
    return all(sid in settled_ids for sid in required)