"""Tests for the tax regime strategy pattern (Phase 1 domain foundation)."""

import sqlite3
from decimal import Decimal

import pytest

from app.tax_regime import (
    LegacyTaxStrategy,
    ResicoStrategy,
    TaxRegimeRegistry,
    TaxResult,
    resolve_bracket,
)


# ---------------------------------------------------------------------------
# resolve_bracket (pure function)
# ---------------------------------------------------------------------------

class TestResolveBracket:
    def test_exact_boundary_25000(self):
        assert resolve_bracket(Decimal("25000")) == Decimal("0.01")

    def test_exact_boundary_50000(self):
        assert resolve_bracket(Decimal("50000")) == Decimal("0.011")

    def test_exact_boundary_83333(self):
        assert resolve_bracket(Decimal("83333")) == Decimal("0.015")

    def test_exact_boundary_166666(self):
        assert resolve_bracket(Decimal("166666")) == Decimal("0.02")

    def test_exact_boundary_2916666(self):
        assert resolve_bracket(Decimal("2916666")) == Decimal("0.025")

    def test_below_first_bracket(self):
        assert resolve_bracket(Decimal("1000")) == Decimal("0.01")

    def test_mid_second_bracket(self):
        assert resolve_bracket(Decimal("40000")) == Decimal("0.011")

    def test_mid_third_bracket(self):
        assert resolve_bracket(Decimal("70000")) == Decimal("0.015")

    def test_mid_fourth_bracket(self):
        assert resolve_bracket(Decimal("100000")) == Decimal("0.02")

    def test_mid_fifth_bracket(self):
        assert resolve_bracket(Decimal("1000000")) == Decimal("0.025")

    def test_above_top_bracket(self):
        assert resolve_bracket(Decimal("5000000")) == Decimal("0.025")

    def test_zero(self):
        assert resolve_bracket(Decimal("0")) == Decimal("0.01")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            resolve_bracket(Decimal("-1"))


# ---------------------------------------------------------------------------
# ResicoStrategy
# ---------------------------------------------------------------------------

class TestResicoStrategy:
    def test_regime_code(self):
        assert ResicoStrategy().get_regime_code() == "RESICO"

    def test_calculate_tax_basic(self):
        result = ResicoStrategy().calculate_tax(Decimal("20000"))
        assert isinstance(result, TaxResult)
        assert result.rate == Decimal("0.01")
        assert result.isr == Decimal("200")
        assert result.gross_mxn == Decimal("20000")
        assert result.regime_code == "RESICO"

    def test_calculate_tax_boundary(self):
        result = ResicoStrategy().calculate_tax(Decimal("83333"))
        assert result.rate == Decimal("0.015")
        assert result.isr == Decimal("1250.00")

    def test_get_brackets(self):
        brackets = ResicoStrategy().get_brackets()
        assert len(brackets) == 5
        assert brackets[0].upper == 25000
        assert brackets[0].rate == Decimal("0.01")

    def test_is_applicable(self):
        assert ResicoStrategy().is_applicable("RESICO") is True
        assert ResicoStrategy().is_applicable("LEGACY_2PCT") is False


# ---------------------------------------------------------------------------
# LegacyTaxStrategy
# ---------------------------------------------------------------------------

class TestLegacyTaxStrategy:
    def test_regime_code(self):
        assert LegacyTaxStrategy().get_regime_code() == "LEGACY_2PCT"

    def test_calculate_tax(self):
        result = LegacyTaxStrategy().calculate_tax(Decimal("10000"))
        assert isinstance(result, TaxResult)
        assert result.rate == Decimal("0.02")
        assert result.isr == Decimal("200")
        assert result.gross_mxn == Decimal("10000")
        assert result.regime_code == "LEGACY_2PCT"

    def test_get_brackets(self):
        assert LegacyTaxStrategy().get_brackets() == []

    def test_is_applicable(self):
        assert LegacyTaxStrategy().is_applicable("LEGACY_2PCT") is True
        assert LegacyTaxStrategy().is_applicable("RESICO") is False


# ---------------------------------------------------------------------------
# TaxRegimeRegistry
# ---------------------------------------------------------------------------

class TestTaxRegimeRegistry:
    def test_register_and_resolve(self):
        registry = TaxRegimeRegistry()
        strategy = ResicoStrategy()
        registry.register(strategy)
        assert registry.resolve("RESICO") is strategy

    def test_resolve_unknown_raises(self):
        registry = TaxRegimeRegistry()
        with pytest.raises(KeyError):
            registry.resolve("UNKNOWN")

    def test_resolve_all(self):
        registry = TaxRegimeRegistry()
        registry.register(ResicoStrategy())
        registry.register(LegacyTaxStrategy())
        assert set(registry.resolve_all().keys()) == {"RESICO", "LEGACY_2PCT"}

    def test_default_registry_has_both(self):
        from app.tax_regime import default_registry
        assert "RESICO" in default_registry.resolve_all()
        assert "LEGACY_2PCT" in default_registry.resolve_all()


# ---------------------------------------------------------------------------
# Schema: tax_regime column
# ---------------------------------------------------------------------------

class TestTaxRegimeSchema:
    def test_new_user_gets_default(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, created_at) VALUES (?, ?, ?, ?, ?)",
            ("u-test", "test@test.com", "Test", "en", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT tax_regime FROM users WHERE sub = 'u-test'").fetchone()
        assert row["tax_regime"] == "LEGACY_2PCT"

    def test_can_set_resico(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, tax_regime, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("u-test", "test@test.com", "Test", "en", "RESICO", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT tax_regime FROM users WHERE sub = 'u-test'").fetchone()
        assert row["tax_regime"] == "RESICO"


# ---------------------------------------------------------------------------
# Schema: foreign_clients table
# ---------------------------------------------------------------------------

class TestForeignClientsSchema:
    def test_create_foreign_client(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, created_at) VALUES (?, ?, ?, ?, ?)",
            ("u-owner", "owner@test.com", "Owner", "en", "2026-01-01T00:00:00Z"),
        )
        db_conn.execute(
            "INSERT INTO foreign_clients (id, owner_user_id, legal_name, tax_id, country, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("fc-test", "u-owner", "Acme Corp", "12-3456789", "USA", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT * FROM foreign_clients WHERE id = 'fc-test'").fetchone()
        assert row["legal_name"] == "Acme Corp"
        assert row["tax_id"] == "12-3456789"
        assert row["country"] == "USA"
        assert row["fiscal_regime"] == "616"
        assert row["uso_cfdi"] == "S01"

    def test_income_source_can_link_to_foreign_client(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, created_at) VALUES (?, ?, ?, ?, ?)",
            ("u-owner", "owner@test.com", "Owner", "en", "2026-01-01T00:00:00Z"),
        )
        db_conn.execute(
            "INSERT INTO foreign_clients (id, owner_user_id, legal_name, tax_id, country, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("fc-test", "u-owner", "Acme Corp", "12-3456789", "USA", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db_conn.execute(
            "INSERT INTO income_sources (id, owner_user_id, foreign_client_id, name, currency, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("s-test", "u-owner", "fc-test", "Consulting", "USD", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT foreign_client_id FROM income_sources WHERE id = 's-test'").fetchone()
        assert row["foreign_client_id"] == "fc-test"

    def test_income_source_without_foreign_client(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, created_at) VALUES (?, ?, ?, ?, ?)",
            ("u-owner", "owner@test.com", "Owner", "en", "2026-01-01T00:00:00Z"),
        )
        db_conn.execute(
            "INSERT INTO income_sources (id, owner_user_id, name, currency, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("s-test", "u-owner", "Consulting", "USD", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT foreign_client_id FROM income_sources WHERE id = 's-test'").fetchone()
        assert row["foreign_client_id"] is None

    def test_cascade_delete_owner(self, db_conn):
        db_conn.execute(
            "INSERT INTO users (sub, email, display_name, language, created_at) VALUES (?, ?, ?, ?, ?)",
            ("u-owner", "owner@test.com", "Owner", "en", "2026-01-01T00:00:00Z"),
        )
        db_conn.execute(
            "INSERT INTO foreign_clients (id, owner_user_id, legal_name, tax_id, country, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("fc-test", "u-owner", "Acme Corp", "12-3456789", "USA", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db_conn.commit()
        # Delete user — FK on foreign_clients should prevent or cascade
        # Since the FK is NOT ON DELETE CASCADE, this should fail
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute("DELETE FROM users WHERE sub = 'u-owner'")
            db_conn.commit()
