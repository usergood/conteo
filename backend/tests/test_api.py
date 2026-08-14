"""Seam 4: API integration through the HTTP boundary (in-memory-free temp DB)."""

import json

import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_me_requires_session(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_dev_login_rejects_bad_token(client):
    r = client.post("/api/auth/dev-login", json={"token": "wrong", "email": "you@example.com"})
    assert r.status_code == 401


def test_dev_login_autocreates_user_and_sets_cookie(client):
    r = client.post("/api/auth/dev-login", json={"token": "test-token", "email": "you@example.com"})
    assert r.status_code == 200
    assert r.cookies.get("conteo_session")
    assert r.json()["user"]["email"] == "you@example.com"
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    payload = me.json()
    assert payload["user"]["language"] == "en"
    assert payload["bank"] is None
    assert payload["sources"] == []


def test_onboarding_gate_bank_settings(client, login):
    login()
    assert client.post("/api/sources", json={"name": "US company", "currency": "USD"}).status_code == 409


def test_new_user_hydrates_guide_status_pending(client, login):
    """Ticket 07: a brand-new user starts with guide_status = 'pending'."""
    login()
    payload = client.get("/api/auth/me").json()
    assert payload["user"]["guideStatus"] == "pending"


def test_guide_status_endpoint_writes_done_and_skipped(client, login):
    """Ticket 07: PUT /api/settings/guide-status persists done/skipped."""
    login()
    assert client.put("/api/settings/guide-status", json={"guideStatus": "done"}).json() == {"guideStatus": "done"}
    assert client.get("/api/auth/me").json()["user"]["guideStatus"] == "done"
    assert client.put("/api/settings/guide-status", json={"guideStatus": "skipped"}).json() == {"guideStatus": "skipped"}
    assert client.get("/api/auth/me").json()["user"]["guideStatus"] == "skipped"


def test_guide_status_rejects_pending_and_unknown(client, login):
    """Ticket 07: the API only ever moves the flag forward to skipped/done."""
    login()
    assert client.put("/api/settings/guide-status", json={"guideStatus": "pending"}).status_code == 422
    assert client.put("/api/settings/guide-status", json={"guideStatus": "wat"}).status_code == 422


def test_guide_status_migration_backfills_existing_bank_users():
    """Ticket 07: guarded migration adds users.guide_status and backfills
    'done' where a bank_settings row exists, 'pending' otherwise. Idempotent."""
    import sqlite3
    from app.db import migrate_guide_status

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (
          sub TEXT PRIMARY KEY, email TEXT NOT NULL, display_name TEXT NOT NULL,
          avatar_url TEXT, language TEXT NOT NULL DEFAULT 'en',
          created_at TEXT NOT NULL, last_login_at TEXT
        );
        CREATE TABLE bank_settings (
          owner_user_id TEXT PRIMARY KEY, currency TEXT NOT NULL DEFAULT 'MXN',
          fixed_fee REAL NOT NULL DEFAULT 320, conv_pct REAL NOT NULL DEFAULT 0,
          tax_pct REAL NOT NULL DEFAULT 2, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        """
    )
    conn.execute("INSERT INTO users (sub,email,display_name,avatar_url,language,created_at,last_login_at) VALUES ('u1','a@b.c','A',NULL,'en','n','n')")
    conn.execute("INSERT INTO users (sub,email,display_name,avatar_url,language,created_at,last_login_at) VALUES ('u2','c@d.e','C',NULL,'en','n','n')")
    conn.execute("INSERT INTO bank_settings (owner_user_id,currency,fixed_fee,conv_pct,tax_pct,created_at,updated_at) VALUES ('u1','MXN',320,3,2,'n','n')")
    conn.commit()

    migrate_guide_status(conn)
    by_sub = {r["sub"]: r["guide_status"] for r in conn.execute("SELECT sub,guide_status FROM users").fetchall()}
    assert by_sub == {"u1": "done", "u2": "pending"}

    # A later bank user who pre-dates a re-run also lands on 'done'.
    conn.execute("INSERT INTO users (sub,email,display_name,avatar_url,language,created_at,last_login_at) VALUES ('u3','f@g.h','F',NULL,'en','n','n')")
    conn.execute("INSERT INTO bank_settings (owner_user_id,currency,fixed_fee,conv_pct,tax_pct,created_at,updated_at) VALUES ('u3','MXN',320,3,2,'n','n')")
    conn.commit()
    migrate_guide_status(conn)
    by_sub = {r["sub"]: r["guide_status"] for r in conn.execute("SELECT sub,guide_status FROM users").fetchall()}
    assert by_sub == {"u1": "done", "u2": "pending", "u3": "done"}

    # An explicit skipped choice is never overridden by a re-run, even with a bank row.
    conn.execute("UPDATE users SET guide_status = 'skipped' WHERE sub = 'u3'")
    conn.commit()
    migrate_guide_status(conn)
    u3 = conn.execute("SELECT guide_status FROM users WHERE sub = 'u3'").fetchone()["guide_status"]
    assert u3 == "skipped"


def test_save_bank_and_hydrate(client, login):
    login()
    r = client.put("/api/settings/bank", json={"fixedFee": 320, "convPct": 3, "taxPct": 2})
    assert r.status_code == 200
    assert r.json()["convPct"] == 3
    me = client.get("/api/auth/me").json()
    assert me["bank"]["fixedFee"] == 320


def test_source_lifecycle(client, onboard):
    onboard()
    created = client.post("/api/sources", json={
        "name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "pct", "commissionValue": 10,
    })
    assert created.status_code == 200
    sid = created.json()["id"]
    sources = client.get("/api/sources").json()
    assert len(sources) == 1
    edited = client.put(f"/api/sources/{sid}", json={
        "name": "US company LLC", "currency": "USD", "fixedSalary": 5000, "commissionMode": "flat", "commissionValue": 600,
    })
    assert edited.json()["name"] == "US company LLC"
    assert edited.json()["commissionMode"] == "flat"


def test_source_delete_requires_empty_and_cascades_shares(client, onboard):
    onboard()
    sid = client.post("/api/sources", json={"name": "S", "currency": "USD"}).json()["id"]
    client.post(f"/api/sources/{sid}/projects", json={
        "name": "P", "value": 1000, "assigned": "2026-08-01", "estEnd": "2026-09-01", "approval": None,
    })
    assert client.delete(f"/api/sources/{sid}").status_code == 409  # has a project
    client.post("/api/shares", json={"sourceId": sid, "email": "wife@gmail.com"})
    # empty the source
    pid = client.get(f"/api/sources/{sid}/projects").json()[0]["id"]
    client.delete(f"/api/projects/{pid}")
    assert client.delete(f"/api/sources/{sid}").status_code == 200
    assert client.get("/api/shares").json()["byMe"] == []


def test_project_inherits_source_currency(client, onboard):
    onboard()
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD"}).json()["id"]
    p = client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website", "value": 8000, "assigned": "2026-08-01", "estEnd": "2026-09-12", "approval": None,
    }).json()
    assert p["sourceId"] == sid


def test_close_view_carries_approval_per_project(client, onboard):
    """The close screen needs each project's approval date to auto-check
    approved-in-month projects (frontend pre-selects them)."""
    onboard()
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD"}).json()["id"]
    client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website", "value": 8000, "assigned": "2026-08-01", "estEnd": "2026-09-12", "approval": "2026-08-05",
    })
    client.post(f"/api/sources/{sid}/projects", json={
        "name": "Other", "value": 1000, "assigned": "2026-08-01", "estEnd": "2026-09-12", "approval": None,
    })
    view = client.get("/api/close?month=2026-08").json()
    proj = {p["name"]: p for p in view["sources"][0]["projects"]}
    assert proj["Website"]["approval"] == "2026-08-05"
    assert proj["Other"]["approval"] is None


def test_shared_months_carry_gross_and_tax(client, onboard, login):
    onboard("owner@gmail.com")
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    client.post("/api/shares", json={"sourceId": sid, "email": "wife@gmail.com"})
    client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 85000, "transfers": 1, "paidProjectIds": []})
    login("wife@gmail.com")
    shared = client.get("/api/months/shared").json()
    assert len(shared) == 1
    assert shared[0]["grossForeign"] == pytest.approx(5000)
    assert shared[0]["bankNet"] == pytest.approx(85000)
    assert shared[0]["tax"] == pytest.approx(1700)


def test_close_month_verified_numbers(client, onboard):
    onboard()
    sid = client.post("/api/sources", json={
        "name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "pct", "commissionValue": 10,
    }).json()["id"]
    pid = client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website redesign", "value": 8000, "assigned": "2026-08-01", "estEnd": "2026-09-12", "approval": None,
    }).json()["id"]
    r = client.post("/api/close", json={
        "month": "2026-08", "sourceId": sid, "typedMxn": 86500, "transfers": 1, "paidProjectIds": [pid],
    })
    assert r.status_code == 200
    st = r.json()
    assert st["derivedRate"] == pytest.approx(15.4319, rel=1e-4)
    assert st["grossMxn"] == pytest.approx(89505, rel=1e-3)
    assert st["netAfterTax"] == pytest.approx(84770)
    assert st["tax"] == pytest.approx(1730)
    assert st["commissionForeign"] == pytest.approx(800)
    # duplicate close rejected
    dup = client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 86500, "transfers": 1, "paidProjectIds": [pid]})
    assert dup.status_code == 409


def test_close_requires_onboarding(client, login):
    login()
    r = client.post("/api/close", json={"month": "2026-08", "sourceId": "x", "typedMxn": 0, "transfers": 1, "paidProjectIds": []})
    assert r.status_code == 409


def test_forecast_uses_fx_snapshot(client, app, seed_fx, onboard):
    seed_fx({"USD": 1, "MXN": 17.06, "SEK": 9.56})
    onboard()
    sid = client.post("/api/sources", json={
        "name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "pct", "commissionValue": 10,
    }).json()["id"]
    client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website", "value": 8000, "assigned": "2026-08-01", "estEnd": "2026-08-20", "approval": None,
    })
    r = client.get("/api/forecast?window=3")
    assert r.status_code == 200
    body = r.json()
    assert len(body["months"]) >= 3
    first = body["months"][0]
    row = first["rows"][0]
    assert row["currency"] == "USD"
    assert row["grossForeign"] == pytest.approx(5000 + 800)  # fixed + 10% of 8000, lands this month
    assert row["grossMxn"] == pytest.approx(5800 * 17.06)
    assert row["bankNet"] == pytest.approx(5800 * 17.06 * 0.97 - 320)


def test_forecast_excludes_source_without_rate(client, app, seed_fx, onboard):
    seed_fx({"USD": 1, "MXN": 17.06})  # no SEK
    onboard()
    for name, cur in [("US company", "USD"), ("Swedish co", "SEK")]:
        client.post("/api/sources", json={"name": name, "currency": cur, "fixedSalary": 1000, "commissionMode": "none", "commissionValue": 0})
    body = client.get("/api/forecast?window=1").json()
    rows = body["months"][0]["rows"]
    usd = next(r for r in rows if r["currency"] == "USD")
    sek = next(r for r in rows if r["currency"] == "SEK")
    assert usd["rateMxn"] == pytest.approx(17.06)
    assert sek["rateMxn"] is None
    assert sek["grossMxn"] is None
    assert body["months"][0]["totals"]["grossMxn"] == pytest.approx(1000 * 17.06)


def test_month_closes_and_mine_lists_it(client, onboard):
    onboard()
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 85000, "transfers": 1, "paidProjectIds": []})
    months = client.get("/api/months/mine").json()
    assert len(months) == 1
    assert months[0]["monthNum"] == 8
    assert months[0]["netTotal"] == pytest.approx(85000 * 0.98)
    assert months[0]["grossByCurrency"] == {"USD": pytest.approx(5000)}
    assert months[0]["bankNet"] == pytest.approx(85000)
    assert months[0]["tax"] == pytest.approx(1700)


def test_forecast_and_close_view_require_bank_settings(client, login):
    """GET /api/forecast and GET /api/close used to crash with a 500 for a
    user without bank settings (bank['fixed_fee'] on None). They must return
    a clean 409 bank_settings_missing instead (ASGI exception fix)."""
    login()
    assert client.get("/api/forecast?window=3").status_code == 409
    assert client.get("/api/close?month=2026-08").status_code == 409


def test_sharing_pending_then_activates(client, onboard, login):
    onboard("owner@gmail.com")
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD"}).json()["id"]
    r = client.post("/api/shares", json={"sourceId": sid, "email": "wife@gmail.com"})
    assert r.status_code == 200
    assert r.json()["status"] == "pending"  # sharee has no account yet
    # owner sees it pending
    assert client.get("/api/shares").json()["byMe"][0]["status"] == "pending"
    # pending shares activate silently at the invitee's first sign-in
    login("wife@gmail.com")
    with_me = client.get("/api/shares").json()["withMe"]
    assert len(with_me) == 1
    assert with_me[0]["status"] == "active"
    assert with_me[0]["email"] == "owner@gmail.com"
    # owner's list flips to active
    login("owner@gmail.com")
    assert client.get("/api/shares").json()["byMe"][0]["status"] == "active"


def test_share_revoke_and_dismiss(client, onboard, login):
    onboard("owner@gmail.com")
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD"}).json()["id"]
    client.post("/api/shares", json={"sourceId": sid, "email": "wife@gmail.com"})
    login("wife@gmail.com")
    share_id = client.get("/api/shares").json()["withMe"][0]["id"]
    # dismiss
    assert client.post(f"/api/shares/{share_id}/dismiss").status_code == 200
    with_me = client.get("/api/shares").json()["withMe"]
    assert with_me[0]["status"] == "dismissed"
    # undismiss
    assert client.post(f"/api/shares/{share_id}/undismiss").status_code == 200
    # owner revokes
    login("owner@gmail.com")
    my_share = client.get("/api/shares").json()["byMe"][0]["id"]
    assert client.post(f"/api/shares/{my_share}/revoke").status_code == 200
    # rejected vanishes from receiver's list but persists for owner
    login("wife@gmail.com")
    assert client.get("/api/shares").json()["withMe"] == []
    login("owner@gmail.com")
    assert client.get("/api/shares").json()["byMe"][0]["status"] == "rejected"


def test_slip_pdf_for_owner(client, app, seed_fx, onboard):
    seed_fx({"USD": 1, "MXN": 17.06, "SEK": 9.56})
    onboard()
    sid = client.post("/api/sources", json={
        "name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "pct", "commissionValue": 10,
    }).json()["id"]
    pid = client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website redesign", "value": 8000, "assigned": "2026-08-01", "estEnd": "2026-09-12", "approval": None,
    }).json()["id"]
    client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 86500, "transfers": 1, "paidProjectIds": [pid]})
    r = client.get("/api/months/2026-08/slip")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"


def test_slip_pdf_denied_for_unshared(client, onboard, login):
    onboard("owner@gmail.com")
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD", "fixedSalary": 1, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 100, "transfers": 1, "paidProjectIds": []})
    login("stranger@gmail.com")
    assert client.get("/api/months/2026-08/slip").status_code == 403


def test_close_fixed_salary_override(client, onboard):
    """Ticket 02: the salary actually paid can be overridden at close."""
    onboard()
    sid = client.post("/api/sources", json={"name": "US company", "currency": "USD", "fixedSalary": 5000, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    r = client.post("/api/close", json={"month": "2026-08", "sourceId": sid, "typedMxn": 43300, "transfers": 1, "paidProjectIds": [], "fixedSalaryOverride": 2500})
    assert r.status_code == 200
    st = r.json()
    assert st["fixedSalaryForeign"] == 2500
    assert st["foreignPaid"] == 2500
    assert st["derivedRate"] == pytest.approx((43300 + 320) / (2500 * 0.97))


def test_forecast_converts_stale_but_present_rate(client, app, seed_fx, onboard):
    """Ticket 04: a cached-fallback rate still converts and is flagged, not dropped."""
    seed_fx({"USD": 1, "MXN": 17.06}, stale=True, source="cached")
    onboard()
    client.post("/api/sources", json={"name": "US company", "currency": "USD", "fixedSalary": 1000, "commissionMode": "none", "commissionValue": 0})
    body = client.get("/api/forecast?window=1").json()
    row = body["months"][0]["rows"][0]
    assert row["rateStale"] is True
    assert row["rateMxn"] == pytest.approx(17.06)
    assert row["grossMxn"] == pytest.approx(1000 * 17.06)
    assert row["bankNet"] is not None


def test_google_callback_denied_redirects(client, app):
    """Ticket 05: Google denial/error bounces the user home with a marker."""
    from fastapi.testclient import TestClient
    with TestClient(app, follow_redirects=False) as c:
        r = c.get("/api/auth/callback?error=access_denied&code=x")
        assert r.status_code == 307
        assert r.headers["location"] == "/?auth_error=google_denied"


def test_google_callback_missing_verifier_redirects(client, app):
    """PKCE verifier lives in a cookie; without it the callback is a no-op."""
    from fastapi.testclient import TestClient
    with TestClient(app, follow_redirects=False) as c:
        r = c.get("/api/auth/callback?code=x")
        assert r.status_code == 307
        assert r.headers["location"] == "/?auth_error=missing_verifier"


def test_google_callback_signs_in_and_sets_session(client, app, monkeypatch):
    """Happy path: exchange the code, upsert the user, activate shares, cookie."""
    from fastapi.testclient import TestClient

    def _fake_exchange(code, verifier, redirect_uri):
        assert code == "authcode"
        assert verifier == "the-verifier"
        return {"id_token": "fake-id-token", "refresh_token": None}

    def _fake_verify(token):
        assert token == "fake-id-token"
        return {"sub": "google:123", "email": "Wife@gmail.com", "name": "Wife"}

    monkeypatch.setattr("app.routers.auth.oauth.exchange_code", _fake_exchange)
    monkeypatch.setattr("app.routers.auth.oauth.verify_id_token", _fake_verify)

    with TestClient(app, follow_redirects=False) as c:
        c.cookies.set("conteo_oauth_verifier", "the-verifier")
        r = c.get("/api/auth/callback?code=authcode")
        assert r.status_code == 307
        assert r.headers["location"] == "http://127.0.0.1:3000/"
        assert r.cookies.get("conteo_session")
        assert not r.cookies.get("conteo_oauth_verifier")
        # the new session is live
        me = c.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "wife@gmail.com"


def test_shared_month_only_when_closed_and_fully_covered(client, onboard, login):
    """Ticket 06: sharee sees a month only when it is closed and they cover every source."""
    onboard("owner@gmail.com")
    a = client.post("/api/sources", json={"name": "US A", "currency": "USD", "fixedSalary": 1000, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    b = client.post("/api/sources", json={"name": "US B", "currency": "USD", "fixedSalary": 1000, "commissionMode": "none", "commissionValue": 0}).json()["id"]
    client.post("/api/shares", json={"sourceId": a, "email": "wife@gmail.com"})
    login("wife@gmail.com")  # activates the share
    login("owner@gmail.com")

    # Month not fully closed (B open) -> nothing shared, slip denied.
    assert client.post("/api/close", json={"month": "2026-08", "sourceId": a, "typedMxn": 50000, "transfers": 1, "paidProjectIds": []}).status_code == 200
    login("wife@gmail.com")
    assert client.get("/api/months/shared").json() == []
    assert client.get("/api/months/2026-08/slip").status_code == 403

    # Closed but sharee doesn't cover B -> still nothing, slip denied.
    login("owner@gmail.com")
    assert client.post("/api/close", json={"month": "2026-08", "sourceId": b, "typedMxn": 50000, "transfers": 1, "paidProjectIds": []}).status_code == 200
    login("wife@gmail.com")
    assert client.get("/api/months/shared").json() == []
    assert client.get("/api/months/2026-08/slip").status_code == 403

    # Share the second source (wife has an account now -> active immediately).
    login("owner@gmail.com")
    assert client.post("/api/shares", json={"sourceId": b, "email": "wife@gmail.com"}).status_code == 200
    login("wife@gmail.com")
    shared = client.get("/api/months/shared").json()
    assert len(shared) == 2
    assert client.get("/api/months/2026-08/slip").status_code == 200