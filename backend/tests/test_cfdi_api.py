"""Tests for CFDI invoice API (tickets 05, 06, 07)."""

import hashlib
import secrets
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.services.months import now_iso

TEST_EMAIL = "you@example.com"


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _login(client, email=TEST_EMAIL):
    return client.post("/api/auth/dev-login", json={"token": "test-token", "email": email})


def _onboard(client, email=TEST_EMAIL):
    _login(client, email)
    return client.put("/api/settings/bank", json={"fixedFee": 320, "convPct": 3, "taxPct": 2})


def _user_sub(email=TEST_EMAIL) -> str:
    return "dev:" + hashlib.sha1(email.encode()).hexdigest()


def _create_foreign_client(client, app, email=TEST_EMAIL):
    """Create a foreign client and income source directly via DB."""
    sub = _user_sub(email)
    conn = sqlite3.connect(app.state.db_path)
    conn.row_factory = sqlite3.Row
    now = now_iso()
    fc_id = "fc" + secrets.token_hex(8)
    src_id = "s" + secrets.token_hex(8)
    # Ensure the user has an issuer_rfc set for CFDI builder
    conn.execute(
        "UPDATE users SET issuer_rfc = ? WHERE sub = ?",
        ("EKU9003173C9", sub),
    )
    conn.execute(
        "INSERT INTO foreign_clients (id, owner_user_id, legal_name, tax_id, country, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fc_id, sub, "Acme Corp", "12-3456789", "USA", now, now),
    )
    conn.execute(
        "INSERT INTO income_sources (id, owner_user_id, foreign_client_id, name, currency, fixed_salary, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (src_id, sub, fc_id, "Consulting", "USD", 5000, now, now),
    )
    conn.commit()
    conn.close()
    return fc_id, src_id


class TestSATCatalogsAPI:
    def test_product_codes_require_auth(self, client):
        r = client.get("/api/sat/product-codes")
        assert r.status_code == 401

    def test_product_codes_listed(self, client, app):
        _onboard(client)
        r = client.get("/api/sat/product-codes")
        assert r.status_code == 200
        codes = r.json()
        assert len(codes) > 10
        assert any(c["clave"] == "80101507" for c in codes)

    def test_unit_codes_listed(self, client, app):
        _onboard(client)
        r = client.get("/api/sat/unit-codes")
        assert r.status_code == 200
        codes = r.json()
        assert len(codes) > 5
        assert any(c["clave"] == "E48" for c in codes)


class TestCFDIInvoiceAPI:
    def test_list_invoices_empty(self, client, app):
        _onboard(client)
        r = client.get("/api/cfdi/invoices")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_invoice_requires_foreign_client(self, client, app):
        _onboard(client)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": "nonexistent",
            "foreignClientId": "nonexistent",
            "month": "2026-01",
            "amountMxn": 1000,
        })
        assert r.status_code == 404

    def test_create_usd_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "currencyOption": "USD",
            "amountMxn": 5000,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "draft"
        assert data["moneda"] == "USD"
        assert data["metodoPago"] == "PPD"
        assert data["total"] == 5000

    def test_create_mxn_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "currencyOption": "MXN",
            "amountMxn": 85000,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["moneda"] == "MXN"
        assert data["metodoPago"] == "PUE"

    def test_duplicate_source_month_rejected(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        assert r.status_code == 409

    def test_update_draft_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        invoice_id = r.json()["id"]
        r = client.put(f"/api/cfdi/invoices/{invoice_id}", json={
            "amountMxn": 6000,
        })
        assert r.status_code == 200
        assert r.json()["total"] == 6000

    def test_delete_draft_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        invoice_id = r.json()["id"]
        r = client.delete(f"/api/cfdi/invoices/{invoice_id}")
        assert r.status_code == 200
        assert r.json()["action"] == "deleted"

    def test_stamp_draft_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        invoice_id = r.json()["id"]
        r = client.post(f"/api/cfdi/invoices/{invoice_id}/stamp")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "stamped"
        assert data["uuid"] is not None

    def test_preview_draft_invoice(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        r = client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        invoice_id = r.json()["id"]
        r = client.post(f"/api/cfdi/invoices/{invoice_id}/preview")
        assert r.status_code == 200
        xml = r.json()["xml"]
        assert "Comprobante" in xml
        assert "4.0" in xml

    def test_list_invoices_with_month_filter(self, client, app):
        _onboard(client)
        fc_id, src_id = _create_foreign_client(client, app)
        client.post("/api/cfdi/invoices", json={
            "sourceId": src_id,
            "foreignClientId": fc_id,
            "month": "2026-01",
            "amountMxn": 5000,
        })
        r = client.get("/api/cfdi/invoices?month=2026-01")
        assert r.status_code == 200
        assert len(r.json()) == 1

        r = client.get("/api/cfdi/invoices?month=2026-02")
        assert r.status_code == 200
        assert len(r.json()) == 0
