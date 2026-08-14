import json
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("DEV_AUTH_TOKEN", "test-token")
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("APP_BASE_URL", "http://127.0.0.1:3000")

from app.main import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    db = str(tmp_path / "test.db")
    return create_app(db_path=db, fx_poll=False)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _conn(app):
    return sqlite3.connect(app.state.db_path)


@pytest.fixture
def seed_fx(app):
    def _seed(rates: dict, fetched_at: str = "2026-08-13T10:00:00Z", stale: bool = False, source: str = "er-api"):
        conn = _conn(app)
        conn.execute(
            "INSERT INTO fx_snapshots (base, rates_json, fetched_at, source, stale) VALUES (?, ?, ?, ?, ?)",
            ("USD", json.dumps(rates), fetched_at, source, int(stale)),
        )
        conn.commit()
        conn.close()
    return _seed


@pytest.fixture
def login(client):
    def _login(email="you@example.com"):
        return client.post("/api/auth/dev-login", json={"token": "test-token", "email": email})
    return _login


@pytest.fixture
def onboard(client, login):
    def _onboard(email="you@example.com"):
        login(email)
        return client.put("/api/settings/bank", json={"fixedFee": 320, "convPct": 3, "taxPct": 2})
    return _onboard