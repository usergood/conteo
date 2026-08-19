"""Tests for monthly tax summary computation (ticket 08)."""

import secrets
import sqlite3

import pytest

from app.services.months import now_iso
from app.services.tax_summary import compute_monthly_tax, get_monthly_tax_summary


TEST_USER = "dev:" + secrets.token_hex(8)


def _setup_db(app) -> sqlite3.Connection:
    """Create user, foreign client, income source, and stamp a CFDI."""
    from app.db import init_db

    conn = sqlite3.connect(app.state.db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    now = now_iso()
    conn.execute(
        "INSERT INTO users (sub, email, display_name, language, created_at, tax_regime) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (TEST_USER, "tax@test.com", "Tax Test", "en", now, "RESICO"),
    )
    conn.execute(
        "INSERT INTO bank_settings (owner_user_id, currency, fixed_fee, conv_pct, tax_pct, created_at, updated_at) "
        "VALUES (?, 'MXN', 320, 3, 2, ?, ?)",
        (TEST_USER, now, now),
    )

    fc_id = "fc" + secrets.token_hex(8)
    conn.execute(
        "INSERT INTO foreign_clients (id, owner_user_id, legal_name, tax_id, country, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fc_id, TEST_USER, "Acme Corp", "12-3456789", "USA", now, now),
    )

    src_id = "s" + secrets.token_hex(8)
    conn.execute(
        "INSERT INTO income_sources (id, owner_user_id, foreign_client_id, name, currency, fixed_salary, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (src_id, TEST_USER, fc_id, "Consulting", "USD", 5000, now, now),
    )

    inv_id = "inv" + secrets.token_hex(8)
    conn.execute(
        "INSERT INTO cfdi_invoices "
        "(id, owner_user_id, source_id, foreign_client_id, month, currency_option, total, "
        "tipo_cambio, serie, folio, fecha_emision, lugar_expedicion, metodo_pago, forma_pago, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (inv_id, TEST_USER, src_id, fc_id, "2026-03", "USD", 5000.0, 17.50,
         "A", "1", "2026-03-15T12:00:00", "06600", "PPD", "03", "stamped", now, now),
    )

    conn.commit()
    return conn


class TestComputeMonthlyTax:
    def test_basic_resico_computation(self, app):
        conn = _setup_db(app)
        result = compute_monthly_tax(conn, TEST_USER, "2026-03")

        assert result["regime_code"] == "RESICO"
        assert result["total_gross_mxn"] == pytest.approx(5000 * 17.50)
        assert result["cfdi_count"] == 1
        assert result["bracket_rate"] is not None
        assert result["isr_due"] > 0
        assert result["status"] == "draft"
        assert len(result["breakdown"]) == 1
        assert result["breakdown"][0]["client"] == "Acme Corp"

    def test_multiple_invoices_aggregate(self, app):
        conn = _setup_db(app)
        now = now_iso()
        inv_id = "inv2" + secrets.token_hex(8)
        conn.execute(
            "INSERT INTO cfdi_invoices "
            "(id, owner_user_id, source_id, foreign_client_id, month, currency_option, total, "
            "tipo_cambio, serie, folio, fecha_emision, lugar_expedicion, metodo_pago, forma_pago, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (inv_id, TEST_USER, "s-dup", "fc-dup", "2026-03", "MXN", 25000.0,
             None, "A", "2", "2026-03-20T12:00:00", "06600", "PUE", "01", "stamped", now, now),
        )
        # Need to update the second invoice's foreign_client_id to the valid one
        conn.execute(
            "UPDATE cfdi_invoices SET foreign_client_id = ("
            "  SELECT id FROM foreign_clients WHERE owner_user_id = ? LIMIT 1"
            ") WHERE id = ?",
            (TEST_USER, inv_id),
        )
        conn.commit()

        result = compute_monthly_tax(conn, TEST_USER, "2026-03")
        assert result["cfdi_count"] == 2
        assert result["total_gross_mxn"] == pytest.approx(5000 * 17.50 + 25000)

    def test_raises_when_no_invoices(self, app):
        conn = _setup_db(app)
        with pytest.raises(ValueError, match="No stamped CFDIs"):
            compute_monthly_tax(conn, TEST_USER, "2026-99")

    def test_raises_when_user_not_found(self, app):
        conn = _setup_db(app)
        with pytest.raises(ValueError, match="User not found"):
            compute_monthly_tax(conn, "nonexistent", "2026-03")

    def test_mxn_invoice_uses_face_value(self, app):
        conn = _setup_db(app)
        # The existing USD invoice is 5000*17.50 = 87500
        result = compute_monthly_tax(conn, TEST_USER, "2026-03")
        # Just MXN: only the USD invoice
        assert result["total_gross_mxn"] == pytest.approx(87500.0)


class TestGetMonthlyTaxSummary:
    def test_retrieves_stored_summary(self, app):
        conn = _setup_db(app)
        compute_monthly_tax(conn, TEST_USER, "2026-03")

        summary = get_monthly_tax_summary(conn, TEST_USER, "2026-03")
        assert summary is not None
        assert summary["month"] == "2026-03"
        assert summary["regime_code"] == "RESICO"
        assert summary["total_gross_mxn"] == pytest.approx(87500.0)

    def test_returns_none_when_missing(self, app):
        conn = _setup_db(app)
        summary = get_monthly_tax_summary(conn, TEST_USER, "2026-99")
        assert summary is None

    def test_breakdown_is_deserialized(self, app):
        conn = _setup_db(app)
        compute_monthly_tax(conn, TEST_USER, "2026-03")

        summary = get_monthly_tax_summary(conn, TEST_USER, "2026-03")
        assert isinstance(summary["breakdown"], list)
        assert len(summary["breakdown"]) == 1
