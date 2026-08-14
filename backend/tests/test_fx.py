import json
from datetime import datetime, timedelta, timezone

import pytest

from app.db import connect, init_db
from app.services import fx


def _seed(conn, rates, now, ago_hours=1):
    fetched = (datetime.fromtimestamp(now, timezone.utc) - timedelta(hours=ago_hours)).isoformat()
    conn.execute(
        "INSERT INTO fx_snapshots (base, rates_json, fetched_at, source, stale) VALUES ('USD', ?, ?, 'test', ?)",
        (json.dumps(rates), fetched, 0),
    )
    conn.commit()


def test_mxn_per_cross_derives_from_usd_base(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    init_db(conn)
    now = datetime.now(timezone.utc).timestamp()
    _seed(conn, {"USD": 1, "MXN": 17.06, "SEK": 9.56}, now)
    rate, stale = fx.mxn_per(conn, "SEK")
    assert stale is False
    assert rate == pytest.approx(17.06 / 9.56)
    rate, stale = fx.mxn_per(conn, "USD")
    assert rate == pytest.approx(17.06)
    rate, stale = fx.mxn_per(conn, "MXN")
    assert rate == pytest.approx(1.0)
    conn.close()


def test_mxn_per_returns_none_when_currency_missing(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    init_db(conn)
    now = datetime.now(timezone.utc).timestamp()
    _seed(conn, {"USD": 1, "MXN": 17.06}, now)
    rate, stale = fx.mxn_per(conn, "SEK")
    assert rate is None
    assert stale is True
    conn.close()


def test_mxn_per_marks_stale_over_48h(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    init_db(conn)
    now = datetime.now(timezone.utc).timestamp()
    _seed(conn, {"USD": 1, "MXN": 17.06}, now, ago_hours=49)
    rate, stale = fx.mxn_per(conn, "USD")
    assert rate is None
    assert stale is True
    conn.close()