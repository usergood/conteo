"""Language selector (ticket 8): defaultLanguage config, and new-user-only
seeding through google-url/callback and dev-login. Existing users keep their
stored language."""


def test_auth_config_returns_default_language(client):
    """defaultLanguage comes from Settings.default_language (default 'en')."""
    r = client.get("/api/auth/config")
    assert r.status_code == 200
    assert r.json()["defaultLanguage"] == "en"


def test_dev_login_seeds_language(client):
    r = client.post("/api/auth/dev-login", json={"token": "test-token", "email": "a@b.c", "language": "es"})
    assert r.status_code == 200
    assert r.json()["user"]["language"] == "es"


def test_dev_login_ignores_invalid_language(client):
    r = client.post("/api/auth/dev-login", json={"token": "test-token", "email": "a@b.c", "language": "fr"})
    assert r.status_code == 200
    assert r.json()["user"]["language"] == "en"


def test_dev_login_defaults_to_en(client):
    r = client.post("/api/auth/dev-login", json={"token": "test-token", "email": "a@b.c"})
    assert r.status_code == 200
    assert r.json()["user"]["language"] == "en"


def test_dev_login_existing_user_keeps_stored_language(client):
    """An existing user's stored language wins over a later login body."""
    client.post("/api/auth/dev-login", json={"token": "test-token", "email": "a@b.c", "language": "es"})
    r = client.post("/api/auth/dev-login", json={"token": "test-token", "email": "a@b.c", "language": "en"})
    assert r.status_code == 200
    assert r.json()["user"]["language"] == "es"


def test_google_url_stashes_valid_lang_cookie(client, app, monkeypatch):
    """?lang=es stashes a cookie (verifier-cookie pattern) for the callback."""
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.routers import auth as auth_router

    monkeypatch.setattr(
        auth_router, "get_settings", lambda: Settings(auth_mode="google", google_client_id="cid")
    )
    monkeypatch.setattr(auth_router.oauth, "new_pkce", lambda: ("verifier", "challenge"))
    monkeypatch.setattr(auth_router.oauth, "google_auth_url", lambda *a: "http://google.example")

    with TestClient(app, follow_redirects=False) as c:
        r = c.get("/api/auth/google-url?lang=es")
        assert r.status_code == 200
        assert c.cookies.get(auth_router.OAUTH_LANG_COOKIE) == "es"


def test_google_url_rejects_unsupported_lang_cookie(client, app, monkeypatch):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.routers import auth as auth_router

    monkeypatch.setattr(
        auth_router, "get_settings", lambda: Settings(auth_mode="google", google_client_id="cid")
    )
    monkeypatch.setattr(auth_router.oauth, "new_pkce", lambda: ("verifier", "challenge"))
    monkeypatch.setattr(auth_router.oauth, "google_auth_url", lambda *a: "http://google.example")

    with TestClient(app, follow_redirects=False) as c:
        r = c.get("/api/auth/google-url?lang=fr")
        assert r.status_code == 200
        assert auth_router.OAUTH_LANG_COOKIE not in c.cookies


def _google_callback_test_client(app, monkeypatch):
    from fastapi.testclient import TestClient

    def _fake_exchange(code, verifier, redirect_uri):
        return {"id_token": "fake-id-token", "refresh_token": None}

    def _fake_verify(token):
        return {"sub": "google:123", "email": "wife@gmail.com", "name": "Wife"}

    monkeypatch.setattr("app.routers.auth.oauth.exchange_code", _fake_exchange)
    monkeypatch.setattr("app.routers.auth.oauth.verify_id_token", _fake_verify)
    return TestClient(app, follow_redirects=False)


def test_google_callback_seeds_new_user_language_from_cookie(client, app, monkeypatch):
    """A new user's pre-login pick (stashed in the lang cookie) seeds their account."""
    with _google_callback_test_client(app, monkeypatch) as c:
        c.cookies.set("conteo_oauth_verifier", "the-verifier")
        c.cookies.set("conteo_oauth_lang", "es")
        r = c.get("/api/auth/callback?code=authcode")
        assert r.status_code == 307
        assert not r.cookies.get("conteo_oauth_lang")  # cookie consumed
        me = c.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["language"] == "es"


def test_google_callback_new_user_defaults_to_en_without_cookie(client, app, monkeypatch):
    with _google_callback_test_client(app, monkeypatch) as c:
        c.cookies.set("conteo_oauth_verifier", "the-verifier")
        c.get("/api/auth/callback?code=authcode")
        me = c.get("/api/auth/me")
        assert me.json()["user"]["language"] == "en"


def test_google_callback_existing_user_keeps_stored_language(client, app, monkeypatch):
    """New-user-only seeding: a stored account language is never overwritten."""
    with _google_callback_test_client(app, monkeypatch) as c:
        # first sign-in creates the user with the pre-login pick
        c.cookies.set("conteo_oauth_verifier", "the-verifier")
        c.cookies.set("conteo_oauth_lang", "es")
        c.get("/api/auth/callback?code=authcode")
        assert c.get("/api/auth/me").json()["user"]["language"] == "es"

        # sign back in (existing user) with a different pick -> stored wins
        c.get("/api/auth/logout")
        c.cookies.set("conteo_oauth_verifier", "the-verifier2")
        c.cookies.set("conteo_oauth_lang", "en")
        c.get("/api/auth/callback?code=authcode2")
        assert c.get("/api/auth/me").json()["user"]["language"] == "es"
