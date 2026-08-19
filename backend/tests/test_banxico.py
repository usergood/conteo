"""Tests for Banxico DOF rate service (ticket 02)."""

import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.banxico import (
    BANXICO_SERIES,
    BANXICO_URL,
    cache_rate,
    fetch_banxico_rate,
    get_cached_rate,
    validate_manual_rate,
)


class TestFetchBanxicoRate:
    def test_returns_none_without_api_key(self):
        assert fetch_banxico_rate(None) is None
        assert fetch_banxico_rate("") is None

    @patch("app.services.banxico.httpx.get")
    def test_returns_rate_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "bmx": {
                "series": [
                    {
                        "idSerie": BANXICO_SERIES,
                        "datos": [
                            {"fecha": "14/08/2026", "dato": "17.0612"},
                            {"fecha": "15/08/2026", "dato": "17.1234"},
                        ],
                    }
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        rate = fetch_banxico_rate("test-key-123")
        assert rate == Decimal("17.1234")
        mock_get.assert_called_once_with(
            BANXICO_URL,
            headers={"Bmx-Token": "test-key-123"},
            params={"tipo": "json"},
            timeout=10,
        )

    @patch("app.services.banxico.httpx.get")
    def test_returns_none_on_empty_series(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"bmx": {"series": []}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert fetch_banxico_rate("key") is None

    @patch("app.services.banxico.httpx.get")
    def test_returns_none_on_empty_datos(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"bmx": {"series": [{"datos": []}]}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert fetch_banxico_rate("key") is None

    @patch("app.services.banxico.httpx.get")
    def test_returns_none_on_network_error(self, mock_get):
        mock_get.side_effect = Exception("connection refused")
        assert fetch_banxico_rate("key") is None

    @patch("app.services.banxico.httpx.get")
    def test_returns_none_on_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_get.return_value = mock_resp

        assert fetch_banxico_rate("key") is None


class TestValidateManualRate:
    def test_accepts_when_no_last_known(self):
        assert validate_manual_rate(Decimal("17.50"), None) is True

    def test_accepts_when_last_known_is_zero(self):
        assert validate_manual_rate(Decimal("17.50"), Decimal("0")) is True

    def test_accepts_within_tolerance(self):
        last = Decimal("17.00")
        # 2% above: 17.34
        proposed = Decimal("17.34")
        assert validate_manual_rate(proposed, last, tolerance_pct=5.0) is True

    def test_rejects_outside_tolerance(self):
        last = Decimal("17.00")
        proposed = Decimal("18.50")  # ~8.8% above
        assert validate_manual_rate(proposed, last, tolerance_pct=5.0) is False

    def test_accepts_at_boundary(self):
        last = Decimal("17.00")
        proposed = Decimal("17.85")  # exactly 5%
        assert validate_manual_rate(proposed, last, tolerance_pct=5.0) is True

    def test_accepts_below_tolerance(self):
        last = Decimal("17.00")
        proposed = Decimal("16.50")  # ~2.9% below
        assert validate_manual_rate(proposed, last, tolerance_pct=5.0) is True

    def test_rejects_below_boundary(self):
        last = Decimal("17.00")
        proposed = Decimal("16.00")  # ~5.9% below
        assert validate_manual_rate(proposed, last, tolerance_pct=5.0) is False

    def test_custom_tolerance(self):
        last = Decimal("100.00")
        proposed = Decimal("115.00")  # 15%
        assert validate_manual_rate(proposed, last, tolerance_pct=20.0) is True
        assert validate_manual_rate(proposed, last, tolerance_pct=10.0) is False


class TestCacheAndGetCachedRate:
    def _make_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE fx_snapshots ("
            "  base TEXT NOT NULL,"
            "  rates_json TEXT NOT NULL,"
            "  fetched_at TEXT NOT NULL,"
            "  source TEXT NOT NULL,"
            "  stale INTEGER NOT NULL DEFAULT 0,"
            "  PRIMARY KEY (base, fetched_at)"
            ")"
        )
        return conn

    def test_cache_and_retrieve(self):
        conn = self._make_conn()
        cache_rate(conn, Decimal("17.1234"))

        cached = get_cached_rate(conn)
        assert cached is not None
        assert cached["rate"] == Decimal("17.1234")

    def test_returns_none_when_empty(self):
        conn = self._make_conn()
        assert get_cached_rate(conn) is None

    def test_returns_none_when_stale(self):
        conn = self._make_conn()
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        conn.execute(
            "INSERT INTO fx_snapshots (base, rates_json, fetched_at, source, stale) "
            "VALUES (?, ?, ?, ?, ?)",
            ("BANXICO_DOF", "17.00", stale_time, "banxico", 0),
        )
        conn.commit()

        assert get_cached_rate(conn) is None

    def test_returns_rate_when_fresh(self):
        conn = self._make_conn()
        fresh_time = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        conn.execute(
            "INSERT INTO fx_snapshots (base, rates_json, fetched_at, source, stale) "
            "VALUES (?, ?, ?, ?, ?)",
            ("BANXICO_DOF", "17.50", fresh_time, "banxico", 0),
        )
        conn.commit()

        cached = get_cached_rate(conn)
        assert cached is not None
        assert cached["rate"] == Decimal("17.50")

    def test_overwrites_previous_cache(self):
        conn = self._make_conn()
        cache_rate(conn, Decimal("17.00"))
        cache_rate(conn, Decimal("17.50"))

        cached = get_cached_rate(conn)
        assert cached is not None
        assert cached["rate"] == Decimal("17.50")
