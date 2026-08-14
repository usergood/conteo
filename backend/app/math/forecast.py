"""Forecast conversion math (pure, no IO).

Per source per month (ticket 04):

    gross_MXN = gross_foreign × live_rate
    bank_net  = gross_MXN × (1 − bank%) − fixed_fee   (one transfer per source)
    net       = bank_net × (1 − tax%)

A source without an available rate (missing or >48h stale — decided by the FX
service before calling here) renders in its own currency with ``gross_mxn``
None and is excluded from the MXN totals. A rate that is present but flagged
stale (cached snapshot) still converts; the flag is for display only.

Totals are computed across all rows that have a rate.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForecastRow:
    source_id: str
    source_name: str
    currency: str
    gross_foreign: float
    rate_mxn: float | None
    rate_stale: bool
    gross_mxn: float | None
    bank_net: float | None
    net_after_tax: float | None


@dataclass(frozen=True)
class ForecastTotals:
    gross_mxn: float = 0
    bank_net: float = 0
    net_after_tax: float = 0


@dataclass(frozen=True)
class Forecast:
    rows: list[ForecastRow] = field(default_factory=list)
    totals: ForecastTotals = field(default_factory=ForecastTotals)


def build(
    rows: list[dict],
    *,
    fixed_fee: float,
    conv_pct: float,
    tax_pct: float,
) -> Forecast:
    """``rows`` are dicts with keys source_id, source_name, currency,
    gross_foreign, rate_mxn (None-able), rate_stale (bool)."""
    built = [forecast_row(r, fixed_fee=fixed_fee, conv_pct=conv_pct, tax_pct=tax_pct) for r in rows]
    convertible = [r for r in built if r.gross_mxn is not None]
    totals = ForecastTotals(
        gross_mxn=sum(r.gross_mxn for r in convertible),
        bank_net=sum(r.bank_net for r in convertible),
        net_after_tax=sum(r.net_after_tax for r in convertible),
    )
    return Forecast(rows=built, totals=totals)


def forecast_row(row: dict, *, fixed_fee: float, conv_pct: float, tax_pct: float) -> ForecastRow:
    gross_foreign = row["gross_foreign"]
    rate = row.get("rate_mxn")
    if rate is None:
        gross = None
        bank_net = None
        net = None
    else:
        gross = gross_foreign * rate
        bank_net = gross * (1 - conv_pct / 100) - fixed_fee
        net = bank_net * (1 - tax_pct / 100)
    return ForecastRow(
        source_id=row["source_id"],
        source_name=row["source_name"],
        currency=row["currency"],
        gross_foreign=gross_foreign,
        rate_mxn=rate,
        rate_stale=bool(row.get("rate_stale", False)),
        gross_mxn=gross,
        bank_net=bank_net,
        net_after_tax=net,
    )
