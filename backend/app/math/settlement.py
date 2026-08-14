"""Month-close settlement math (pure, no IO).

Derives the bank's effective FX rate from the exact MXN that hit the account.

    rate = (typed MXN + transfers × fixed fee) ÷ (foreign paid × (1 − bank %))
    tax  = typed MXN × taxPct%
    net after tax = typed MXN − tax

The gross MXN recorded for a settlement is converted at the *derived* rate
(ticket 10), so the slip is internally consistent: bank fee = gross − typed
equals the % take plus the fixed fees, and the round-trip check is 0 by
construction. When nothing foreign was paid the derived rate is unknown
(None) and is displayed as "—".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settlement:
    """The derived numbers for one source-month close.

    ``gross_mxn``, ``derived_rate`` and ``bank_kept`` are None when
    ``foreign_paid`` is zero (nothing to convert — the rate is unknowable).
    """

    foreign_paid: float
    typed_mxn: float
    transfers: int
    fixed_fee: float
    conv_pct: float
    tax_pct: float

    fees: float
    foreign_net: float
    derived_rate: float | None
    gross_mxn: float | None
    bank_pct_take: float | None
    bank_kept: float | None
    tax: float
    net_after_tax: float
    round_trip: float | None


def derive(
    *,
    typed_mxn: float,
    foreign_paid: float,
    transfers: int = 1,
    fixed_fee: float = 320,
    conv_pct: float = 3,
    tax_pct: float = 2,
) -> Settlement:
    fees = transfers * fixed_fee
    foreign_net = foreign_paid * (1 - conv_pct / 100)
    convertible = foreign_paid > 0 and foreign_net > 0

    rate = (typed_mxn + fees) / foreign_net if convertible else None
    gross = rate * foreign_paid if rate is not None else None
    bank_pct_take = gross * conv_pct / 100 if gross is not None else None
    bank_kept = gross - typed_mxn if gross is not None else None
    tax = typed_mxn * tax_pct / 100
    net_after_tax = typed_mxn - tax
    round_trip = (
        rate * foreign_paid * (1 - conv_pct / 100) - fees - typed_mxn
        if rate is not None
        else None
    )

    return Settlement(
        foreign_paid=foreign_paid,
        typed_mxn=typed_mxn,
        transfers=transfers,
        fixed_fee=fixed_fee,
        conv_pct=conv_pct,
        tax_pct=tax_pct,
        fees=fees,
        foreign_net=foreign_net,
        derived_rate=rate,
        gross_mxn=gross,
        bank_pct_take=bank_pct_take,
        bank_kept=bank_kept,
        tax=tax,
        net_after_tax=net_after_tax,
        round_trip=round_trip,
    )
