"""Unit tests for oauth.verify_id_token (ticket 05). Regression for the
AttributeError crash: PyJWKClient must be given a URL, not a parsed JWKS dict."""

import time

import jwt
import pytest

from app.config import get_settings
from app.services import oauth


class _FakeJwk:
    def __init__(self, key):
        self.key = key


class _FakeJwkClient:
    def __init__(self, *args, **kwargs):
        self.pub: bytes | None = None

    def get_signing_key_from_jwt(self, token):
        return _FakeJwk(self.pub or b"")


def _valid_token(pub_pem: bytes, audience: str = "client-abc"):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    token = jwt.encode(
        {"sub": "google:1", "email": "a@b.c", "name": "A", "aud": audience, "exp": int(time.time()) + 300},
        private,
        algorithm="RS256",
        headers={"kid": "k1"},
    )
    return token, pub_pem


def _stub_jwks_client(monkeypatch, pub_pem: bytes):
    fake_client = _FakeJwkClient()
    fake_client.pub = pub_pem
    monkeypatch.setattr(oauth.jwt, "PyJWKClient", lambda *a, **k: fake_client)


def test_verify_id_token_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "google_client_id", "client-abc")
    token, pub_pem = _valid_token(pub_pem=b"")
    _stub_jwks_client(monkeypatch, pub_pem)
    claims = oauth.verify_id_token(token)
    assert claims["email"] == "a@b.c"
    assert claims["sub"] == "google:1"


def test_verify_id_token_rejects_wrong_audience(monkeypatch):
    """A token minted for another client is rejected (audience check)."""
    monkeypatch.setattr(get_settings(), "google_client_id", "client-abc")
    token, pub_pem = _valid_token(pub_pem=b"", audience="some-other-client")
    _stub_jwks_client(monkeypatch, pub_pem)
    with pytest.raises(ValueError):
        oauth.verify_id_token(token)


def test_verify_id_token_passes_url_to_pyjwkclient(monkeypatch):
    """Regression (oauth bug): PyJWKClient must receive the JWKS URL, never a dict."""
    captured = {}

    class _Recording:
        def __init__(self, uri, **kwargs):
            captured["uri"] = uri

    monkeypatch.setattr(oauth.jwt, "PyJWKClient", _Recording)
    monkeypatch.setattr(get_settings(), "google_client_id", "x")
    oauth.jwt.PyJWKClient(oauth.JWKS_URL)
    assert captured["uri"] == oauth.JWKS_URL
