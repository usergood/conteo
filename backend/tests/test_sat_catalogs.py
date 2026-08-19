"""Tests for SAT catalog codes (ticket 04)."""

import sqlite3
from datetime import date

import pytest

from app.db import init_db
from app.services.sat_catalogs import (
    seed_catalogs,
    validate_product_code,
    validate_unit_code,
    list_product_codes,
    list_unit_codes,
    PRODUCT_CODES,
    UNIT_CODES,
)


@pytest.fixture
def seeded_db(app):
    """DB with initialized schema and seeded SAT catalogs."""
    conn = sqlite3.connect(app.state.db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    seed_catalogs(conn)
    yield conn
    conn.close()


class TestSeedCatalogs:
    def test_seeds_product_codes(self, seeded_db):
        rows = seeded_db.execute("SELECT COUNT(*) AS n FROM sat_product_codes").fetchone()
        assert rows["n"] == len(PRODUCT_CODES)

    def test_seeds_unit_codes(self, seeded_db):
        rows = seeded_db.execute("SELECT COUNT(*) AS n FROM sat_unit_codes").fetchone()
        assert rows["n"] == len(UNIT_CODES)

    def test_idempotent(self, seeded_db):
        seed_catalogs(seeded_db)
        rows = seeded_db.execute("SELECT COUNT(*) AS n FROM sat_product_codes").fetchone()
        assert rows["n"] == len(PRODUCT_CODES)

    def test_it_consulting_code_exists(self, seeded_db):
        assert validate_product_code(seeded_db, "80101507")

    def test_invalid_code_rejected(self, seeded_db):
        assert not validate_product_code(seeded_db, "99999999")


class TestValidateProductCode:
    def test_active_code(self, seeded_db):
        assert validate_product_code(seeded_db, "80101507")

    def test_inactive_code(self, seeded_db):
        seeded_db.execute(
            "INSERT INTO sat_product_codes (clave, description, category, vigencia_inicio, vigencia_fin, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("99999999", "Test", "test", "2020-01-01", "2020-12-31", "2020-01-01"),
        )
        seeded_db.commit()
        assert not validate_product_code(seeded_db, "99999999")


class TestValidateUnitCode:
    def test_active_code(self, seeded_db):
        assert validate_unit_code(seeded_db, "E48")

    def test_invalid_code(self, seeded_db):
        assert not validate_unit_code(seeded_db, "INVALID")


class TestListCodes:
    def test_list_product_codes(self, seeded_db):
        codes = list_product_codes(seeded_db, active_only=True)
        assert len(codes) == len(PRODUCT_CODES)
        assert all("clave" in c and "description" in c for c in codes)

    def test_list_unit_codes(self, seeded_db):
        codes = list_unit_codes(seeded_db, active_only=True)
        assert len(codes) == len(UNIT_CODES)
