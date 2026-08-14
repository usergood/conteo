"""Seam 1: settlement.derive() — the month-close settlement math.

Spec: rate = (typed MXN + transfers × fixed fee) ÷ (foreign paid × (1 − bank %))
      tax  = typed MXN × taxPct%
      net after tax = typed MXN − tax

Verified smoke numbers (handoff, prototype v3): source USD $5000 fixed + $800
project commission @10%, typed 86,500 MXN, 1 transfer, fee 320, bank 3%, tax 2%
→ rate 15.4319, net 84,770. Round-trip = 0.00 by construction.

The settlement's gross MXN is converted at the *derived* rate (ticket 10:
"gross source-currency total → MXN at that settlement's derived FX rate").
"""

import pytest

from app.math.settlement import derive


def settle(**kw):
    return derive(
        typed_mxn=kw.get("typed_mxn", 0),
        foreign_paid=kw.get("foreign_paid", 0),
        transfers=kw.get("transfers", 1),
        fixed_fee=kw.get("fixed_fee", 320),
        conv_pct=kw.get("conv_pct", 3),
        tax_pct=kw.get("tax_pct", 2),
    )


def test_verified_smoke_numbers():
    d = settle(foreign_paid=5800, typed_mxn=86500, transfers=1, fixed_fee=320, conv_pct=3, tax_pct=2)
    assert d.derived_rate == pytest.approx(15.4319, rel=1e-4)
    assert d.gross_mxn == pytest.approx(89505, rel=1e-3)
    assert d.tax == pytest.approx(1730)
    assert d.net_after_tax == pytest.approx(84770)
    assert d.round_trip == pytest.approx(0.0, abs=0.001)


def test_single_transfer_scenario():
    d = settle(foreign_paid=2500, typed_mxn=43000, transfers=1)
    assert d.fees == 320
    assert d.foreign_net == pytest.approx(2425.0)
    assert d.derived_rate == pytest.approx((43000 + 320) / 2425.0)
    assert d.bank_kept == pytest.approx(d.gross_mxn - 43000)


def test_multiple_transfers_blend_to_same_rate_as_single():
    single = settle(foreign_paid=5000, typed_mxn=86000, transfers=1)
    multi = settle(foreign_paid=5000, typed_mxn=86000, transfers=2)
    assert multi.derived_rate == pytest.approx((86000 + 640) / 4850.0)
    assert multi.fees == 640


def test_one_vs_per_project_toggle_moves_rate():
    one = settle(foreign_paid=4500, typed_mxn=77400, transfers=1)
    many = settle(foreign_paid=4500, typed_mxn=77400, transfers=3)
    assert many.derived_rate != one.derived_rate
    assert many.fees == 3 * 320


def test_zero_foreign_paid_yields_null_rate():
    d = settle(foreign_paid=0, typed_mxn=0)
    assert d.derived_rate is None
    assert d.gross_mxn is None
    assert d.bank_kept is None
    assert d.tax == 0
    assert d.net_after_tax == 0


def test_bank_pct_accepts_decimals():
    d = settle(foreign_paid=2500, typed_mxn=43000, conv_pct=1.5, fixed_fee=0)
    assert d.foreign_net == pytest.approx(2462.5)
    assert d.derived_rate == pytest.approx(43000 / 2462.5)


def test_tax_affects_only_slip_not_rate():
    a = settle(foreign_paid=2500, typed_mxn=43000, tax_pct=2)
    b = settle(foreign_paid=2500, typed_mxn=43000, tax_pct=5)
    assert a.derived_rate == b.derived_rate
    assert a.net_after_tax == pytest.approx(43000 * 0.98)
    assert b.net_after_tax == pytest.approx(43000 * 0.95)


def test_round_trip_is_zero_by_construction():
    d = settle(foreign_paid=1234.56, typed_mxn=19999.99, transfers=2, fixed_fee=320, conv_pct=3, tax_pct=2)
    assert d.round_trip == pytest.approx(0.0, abs=0.001)
