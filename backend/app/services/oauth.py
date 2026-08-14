"""Google Sign-In, backend OAuth authorization-code + PKCE (ticket 05).

Scopes: openid email profile. Client secret is server-side only; the frontend
never sees Google tokens. The ID token is verified against Google's JWKS.
"""

import base64
import hashlib
import os
import time

import httpx
import jwt

from ..config import get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"


def new_pkce() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge)."""
    verifier = base64.urlsafe_b64encode(os.urandom(48)).rstrip(b"=").decode()
    return verifier, challenge_for(verifier)


def challenge_for(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def google_auth_url(verifier: str, redirect_uri: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "code_challenge": challenge_for(verifier),
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={_quote(v)}" for k, v in params.items())
    return f"{AUTH_URL}?{query}"


def _quote(value: str) -> str:
    import urllib.parse

    return urllib.parse.quote(value, safe="")


def exchange_code(code: str, code_verifier: str, redirect_uri: str) -> dict:
    """Swap the auth code for tokens. Raises httpx.HTTPError on failure."""
    settings = get_settings()
    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }
    with httpx.Client(timeout=15) as client:
        resp = client.post(TOKEN_URL, data=payload)
        resp.raise_for_status()
        return resp.json()


def verify_id_token(id_token: str) -> dict:
    """Verify the Google ID token and return its claims."""
    settings = get_settings()
    jwks_client = jwt.PyJWKClient(JWKS_URL, timeout=15)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(id_token).key
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            options={"verify_exp": True},
        )
    except jwt.PyJWTError as exc:
        raise ValueError(f"invalid id_token: {exc}") from exc
    return claims


def revoke_refresh_token(refresh_token: str) -> None:
    try:
        with httpx.Client(timeout=10) as client:
            client.post(REVOKE_URL, data={"token": refresh_token})
    except httpx.HTTPError:
        pass
