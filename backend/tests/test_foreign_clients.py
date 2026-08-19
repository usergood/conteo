"""Tests for foreign clients CRUD API (decision #24)."""

import pytest


class TestForeignClientCRUD:
    def test_list_empty(self, client, login):
        login()
        r = client.get("/api/foreign-clients")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_foreign_client(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["legalName"] == "Acme Corp"
        assert body["taxId"] == "12-3456789"
        assert body["country"] == "USA"
        assert body["rfc"] == "XEXX010101000"
        assert body["fiscalRegime"] == "616"
        assert body["usoCfdi"] == "S01"
        assert body["currencyOption"] == "USD"

    def test_list_returns_created(self, client, login):
        login()
        client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        r = client.get("/api/foreign-clients")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_update_foreign_client(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        fc_id = r.json()["id"]
        r = client.put(f"/api/foreign-clients/{fc_id}", json={
            "legalName": "Acme Inc",
        })
        assert r.status_code == 200
        assert r.json()["legalName"] == "Acme Inc"
        assert r.json()["taxId"] == "12-3456789"  # unchanged

    def test_update_currency_option(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        fc_id = r.json()["id"]
        r = client.put(f"/api/foreign-clients/{fc_id}", json={
            "currencyOption": "MXN",
        })
        assert r.status_code == 200
        assert r.json()["currencyOption"] == "MXN"

    def test_delete_foreign_client(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        fc_id = r.json()["id"]
        r = client.delete(f"/api/foreign-clients/{fc_id}")
        assert r.status_code == 200
        assert r.json()["ok"] is True
        # Verify deleted
        r = client.get("/api/foreign-clients")
        assert r.json() == []

    def test_delete_foreign_client_linked_to_source(self, client, onboard):
        onboard()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        fc_id = r.json()["id"]
        # Create source linked to foreign client (requires onboarded)
        r = client.post("/api/sources", json={
            "name": "Consulting",
            "currency": "USD",
            "foreignClientId": fc_id,
        })
        assert r.status_code == 200, r.json()
        # Try to delete - should fail because linked
        r = client.delete(f"/api/foreign-clients/{fc_id}")
        assert r.status_code == 409
        assert r.json()["detail"] == "foreign_client_in_use"

    def test_get_foreign_client(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={
            "legalName": "Acme Corp",
            "taxId": "12-3456789",
            "country": "USA",
        })
        fc_id = r.json()["id"]
        r = client.get(f"/api/foreign-clients/{fc_id}")
        assert r.status_code == 200
        assert r.json()["id"] == fc_id

    def test_get_nonexistent(self, client, login):
        login()
        r = client.get("/api/foreign-clients/fc-nonexistent")
        assert r.status_code == 404

    def test_requires_auth(self, client):
        r = client.get("/api/foreign-clients")
        assert r.status_code in (401, 403)

    def test_create_validates_required_fields(self, client, login):
        login()
        r = client.post("/api/foreign-clients", json={})
        assert r.status_code == 422
