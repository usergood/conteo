"""Auth router — Google OAuth (PKCE), dev-login bypass, sessions (ticket 05)."""

import hashlib
import secrets
from datetime import datetime, timezone

import httpx
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ..auth import (
    cookie_name,
    create_session,
    delete_session,
    get_db_conn,
    get_session_user,
)
from ..config import get_settings
from ..serializers import user_dict
from ..services import hydrate, oauth
from ..services.months import now_iso

router = APIRouter(prefix="/api/auth", tags=["auth"])

OAUTH_VERIFIER_COOKIE = "conteo_oauth_verifier"


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=cookie_name(),
        value=token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=cookie_name(), path="/")


def _redirect_uri() -> str:
    return f"{get_settings().app_base_url.rstrip('/')}/api/auth/callback"


def _upsert_user(conn: sqlite3.Connection, sub: str, email: str, display_name: str, avatar_url: str | None) -> None:
    existing = conn.execute("SELECT sub FROM users WHERE sub = ?", (sub,)).fetchone()
    now = now_iso()
    if existing:
        conn.execute(
            "UPDATE users SET email = ?, display_name = ?, avatar_url = ?, last_login_at = ? WHERE sub = ?",
            (email, display_name, avatar_url, now, sub),
        )
    else:
        conn.execute(
            "INSERT INTO users (sub, email, display_name, avatar_url, language, created_at, last_login_at) "
            "VALUES (?, ?, ?, ?, 'en', ?, ?)",
            (sub, email, display_name, avatar_url, now, now),
        )
    conn.commit()


def _activate_pending_shares(conn: sqlite3.Connection, email: str, sub: str) -> None:
    """Pending shares silently activate at the invitee's first sign-in (06)."""
    conn.execute(
        "UPDATE shares SET sharee_user_id = ?, status = 'active', updated_at = ? "
        "WHERE LOWER(pending_email) = LOWER(?) AND status = 'pending'",
        (sub, now_iso(), email),
    )
    conn.commit()


class DevLoginBody(BaseModel):
    token: str
    email: str


@router.get("/config")
def auth_config():
    settings = get_settings()
    return {
        "authMode": settings.auth_mode,
        "googleClientId": settings.google_client_id,
        "devLoginEnabled": bool(settings.dev_auth_token),
    }


@router.get("/google-url")
def google_url(response: Response):
    if get_settings().auth_mode != "google":
        raise HTTPException(status_code=403, detail="google_auth_disabled")
    verifier, _ = oauth.new_pkce()
    settings = get_settings()
    response.set_cookie(
        key=OAUTH_VERIFIER_COOKIE,
        value=verifier,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )
    return {"url": oauth.google_auth_url(verifier, _redirect_uri())}


@router.get("/callback")
def google_callback(
    request: Request,
    code: str,
    error: str | None = None,
    conn: sqlite3.Connection = Depends(get_db_conn),
):
    """Google redirect target. Completes PKCE using the verifier we stashed in a
    cookie before the redirect, then signs the user in (ticket 05)."""
    if error or not code:
        return RedirectResponse(url="/?auth_error=google_denied")
    verifier = request.cookies.get(OAUTH_VERIFIER_COOKIE)
    if not verifier:
        return RedirectResponse(url="/?auth_error=missing_verifier")
    try:
        tokens = oauth.exchange_code(code, verifier, _redirect_uri())
        claims = oauth.verify_id_token(tokens["id_token"])
    except (httpx.HTTPError, ValueError):
        return RedirectResponse(url="/?auth_error=google_login_failed")
    sub = claims["sub"]
    email = claims.get("email", "").lower()
    display_name = claims.get("name", email.split("@")[0])
    avatar = claims.get("picture")
    _upsert_user(conn, sub, email, display_name, avatar)
    _activate_pending_shares(conn, email, sub)
    refresh = tokens.get("refresh_token")
    if refresh:
        conn.execute(
            "INSERT INTO auth_tokens (user_id, google_refresh_token, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET google_refresh_token = excluded.google_refresh_token, updated_at = excluded.updated_at",
            (sub, refresh, now_iso()),
        )
        conn.commit()
    token = create_session(conn, sub)
    settings = get_settings()
    response = RedirectResponse(url=settings.app_base_url.rstrip("/") + "/")
    _set_session_cookie(response, token)
    response.delete_cookie(key=OAUTH_VERIFIER_COOKIE, path="/")
    return response


@router.post("/dev-login")
def dev_login(body: DevLoginBody, response: Response, conn: sqlite3.Connection = Depends(get_db_conn)):
    settings = get_settings()
    if settings.auth_mode != "dev" or not settings.dev_auth_token:
        raise HTTPException(status_code=403, detail="dev_login_disabled")
    if not secrets.compare_digest(body.token, settings.dev_auth_token):
        raise HTTPException(status_code=401, detail="invalid_token")
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="invalid_email")
    sub = "dev:" + hashlib.sha1(email.encode()).hexdigest()
    display_name = email.split("@")[0]
    _upsert_user(conn, sub, email, display_name, None)
    _activate_pending_shares(conn, email, sub)
    token = create_session(conn, sub)
    _set_session_cookie(response, token)
    row = conn.execute("SELECT * FROM users WHERE sub = ?", (sub,)).fetchone()
    return {"user": user_dict(row)}


@router.get("/me")
def me(request: Request, conn: sqlite3.Connection = Depends(get_db_conn)):
    token = request.cookies.get(cookie_name())
    session = get_session_user(conn, token) if token else None
    if session is None:
        raise HTTPException(status_code=401, detail="not_signed_in")
    return hydrate.hydrate_payload(conn, session["user_id"])


@router.post("/logout")
def logout(request: Request, response: Response, conn: sqlite3.Connection = Depends(get_db_conn)):
    token = request.cookies.get(cookie_name())
    if token:
        session = get_session_user(conn, token)
        if session:
            refresh = conn.execute(
                "SELECT google_refresh_token FROM auth_tokens WHERE user_id = ?", (session["user_id"],)
            ).fetchone()
            if refresh and refresh["google_refresh_token"]:
                oauth.revoke_refresh_token(refresh["google_refresh_token"])
        delete_session(conn, token)
    _clear_session_cookie(response)
    return {"ok": True}