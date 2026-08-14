"""Seam 2: forecast.build() — per-source forecast conversion + totals.

Spec (ticket 04): per source per month —
    gross_MXN   = gross_foreign × live_rate
    bank_net    = gross_MXN × (1 − bank%) − fixed_fee   (one transfer per source)
    net         = bank_net × (1 − tax%)

No recent rate (>48h stale or missing) → that source renders in its own
currency, excluded from MXN totals. A rate present but flagged stale (cached
snapshot, 24–48h) still converts, with a warning. 2 decimals are a display
concern (Intl) — the math keeps full precision.
"""

import pytest

from app.math.forecast import build


def src(**kw):
    return {
        "source_id": kw.get("source_id", "s1"),
        "source_name": kw.get("source_name", "US company"),
        "currency": kw.get("currency", "USD"),
        "gross_foreign": kw.get("gross_foreign", 0),
        "rate_mxn": kw.get("rate_mxn", None),
        "rate_stale": kw.get("rate_stale", False),
    }


def test_verified_smoke_numbers():
    f = build([src(gross_foreign=5800, rate_mxn=17.06)], fixed_fee=320, conv_pct=3, tax_pct=2)
    row = f.rows[0]
    assert row.gross_mxn == pytest.approx(98948)
    assert row.bank_net == pytest.approx(98948 * 0.97 - 320)
    assert row.net_after_tax == pytest.approx((98948 * 0.97 - 320) * 0.98)
    assert f.totals.gross_mxn == pytest.approx(98948)
    assert f.totals.bank_net == pytest.approx(98948 * 0.97 - 320)
    assert f.totals.net_after_tax == pytest.approx((98948 * 0.97 - 320) * 0.98)


def test_one_fixed_fee_per_source():
    f = build([src(gross_foreign=1000, rate_mxn=10)], fixed_fee=320, conv_pct=3, tax_pct=2)
    assert f.rows[0].bank_net == pytest.approx(1000 * 10 * 0.97 - 320)


def test_source_without_rate_renders_own_currency_excluded_from_totals():
    f = build(
        [
            src(source_id="s1", gross_foreign=5800, rate_mxn=17.06),
            src(source_id="s2", source_name="Swedish co", currency="SEK", gross_foreign=9000, rate_mxn=None),
        ],
        fixed_fee=320, conv_pct=3, tax_pct=2,
    )
    own = f.rows[1]
    assert own.gross_mxn is None
    assert own.bank_net is None
    assert own.net_after_tax is None
    assert f.totals.gross_mxn == pytest.approx(98948)


def test_stale_but_present_rate_still_converts_and_is_flagged():
    f = build([src(gross_foreign=5800, rate_mxn=17.06, rate_stale=True)], fixed_fee=320, conv_pct=3, tax_pct=2)
    assert f.rows[0].rate_stale is True
    assert f.rows[0].gross_mxn == pytest.approx(98948)
    assert f.totals.gross_mxn == pytest.approx(98948)


def test_totals_sum_multiple_sources():
    f = build(
        [
            src(source_id="s1", gross_foreign=1000, rate_mxn=10),
            src(source_id="s2", source_name="Swedish co", currency="SEK", gross_foreign=2000, rate_mxn=1.5),
        ],
        fixed_fee=320, conv_pct=3, tax_pct=2,
    )
    gross = 1000 * 10 + 2000 * 1.5
    bank = (10000 * 0.97 - 320) + (3000 * 0.97 - 320)
    assert f.totals.gross_mxn == pytest.approx(gross)
    assert f.totals.bank_net == pytest.approx(bank)


def test_no_sources_yields_empty_totals():
    f = build([], fixed_fee=320, conv_pct=3, tax_pct=2)
    assert f.rows == []
    assert f.totals.gross_mxn == 0
    assert f.totals.bank_net == 0
    assert f.totals.net_after_tax == 0
