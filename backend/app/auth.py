"""Server-side sessions + the current-user FastAPI dependency (ticket 05).

Opaque HttpOnly/SameSite=Lax cookie bound to a `sessions` row; ~30-day sliding
expiry (the row's expires_at slides on each request while the session lives).
The token is random and stored only server-side.
"""

import secrets
from datetime import datetime, timedelta, timezone

import sqlite3
from fastapi import Cookie, Depends, HTTPException, Request

from .config import get_settings
from .db import connect, default_db_path
from .services.months import now_iso


def cookie_name() -> str:
    return "conteo_session"


def create_session(conn: sqlite3.Connection, user_id: str) -> str:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=settings.session_days)
    conn.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now_iso(), expires.isoformat()),
    )
    conn.commit()
    return token


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE id = ?", (token,))
    conn.commit()


def get_session_user(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    row = conn.execute(
        "SELECT s.*, u.email, u.display_name, u.avatar_url, u.language "
        "FROM sessions s JOIN users u ON u.sub = s.user_id WHERE s.id = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    expires = datetime.fromisoformat(row["expires_at"])
    if expires < datetime.now(timezone.utc):
        delete_session(conn, token)
        return None
    # Sliding expiry: bump on each authenticated request.
    settings = get_settings()
    new_expires = datetime.now(timezone.utc) + timedelta(days=settings.session_days)
    conn.execute(
        "UPDATE sessions SET expires_at = ?, last_seen_at = ? WHERE id = ?",
        (new_expires.isoformat(), now_iso(), token),
    )
    conn.commit()
    return row


def current_session_id(cookie: str | None = Cookie(default=None, alias=cookie_name())) -> str | None:
    return cookie


def get_db_conn(request: Request):
    db_path = getattr(request.app.state, "db_path", None) or default_db_path()
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


class CurrentUser:
    def __init__(self, sub: str, email: str, display_name: str, avatar_url: str | None, language: str):
        self.sub = sub
        self.email = email
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.language = language

    def __repr__(self) -> str:
        return f"<CurrentUser {self.email}>"


def require_user(
    conn: sqlite3.Connection = Depends(get_db_conn),
    token: str | None = Depends(current_session_id),
) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=401, detail="not_signed_in")
    row = get_session_user(conn, token)
    if row is None:
        raise HTTPException(status_code=401, detail="session_expired")
    return CurrentUser(
        sub=row["user_id"],
        email=row["email"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        language=row["language"],
    )


def get_bank_settings(conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT currency, fixed_fee, conv_pct, tax_pct FROM bank_settings WHERE owner_user_id = ?",
        (user_id,),
    ).fetchone()


def require_onboarded(
    conn: sqlite3.Connection = Depends(get_db_conn),
    user: CurrentUser = Depends(require_user),
) -> sqlite3.Row:
    """Bank settings must exist before source/close/forecast work (ticket 10)."""
    bank = get_bank_settings(conn, user.sub)
    if bank is None:
        raise HTTPException(status_code=409, detail="bank_settings_missing")
    return bank
