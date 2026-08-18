"""Tax regime strategy pattern (ticket 29).

Multi-regime extensibility: RESICO first, legacy 2% as deprecated fallback.
Each regime implements TaxRegimeStrategy; the registry maps regime_code → strategy.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaxResult:
    gross_mxn: Decimal
    rate: Decimal
    isr: Decimal
    regime_code: str


# ---------------------------------------------------------------------------
# Strategy protocol
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaxBracket:
    upper: int  # inclusive upper bound (0 = no upper bound)
    rate: Decimal


class TaxRegimeStrategy(Protocol):
    def calculate_tax(self, gross_mxn: Decimal) -> TaxResult: ...
    def get_brackets(self) -> list[TaxBracket]: ...
    def get_regime_code(self) -> str: ...
    def is_applicable(self, regime_code: str) -> bool: ...


# ---------------------------------------------------------------------------
# Bracket lookup
# ---------------------------------------------------------------------------

_RESICO_BRACKETS: list[TaxBracket] = [
    TaxBracket(upper=25_000, rate=Decimal("0.01")),
    TaxBracket(upper=50_000, rate=Decimal("0.011")),
    TaxBracket(upper=83_333, rate=Decimal("0.015")),
    TaxBracket(upper=166_666, rate=Decimal("0.02")),
    TaxBracket(upper=2_916_666, rate=Decimal("0.025")),
    TaxBracket(upper=0, rate=Decimal("0.025")),  # unbounded top bracket
]


def resolve_bracket(gross_mxn: Decimal) -> Decimal:
    """Return the RESICO ISR rate for a given monthly gross MXN (Art. 113-E LISR)."""
    if gross_mxn < 0:
        raise ValueError("gross_mxn must be non-negative")
    for bracket in _RESICO_BRACKETS:
        if bracket.upper == 0 or gross_mxn <= bracket.upper:
            return bracket.rate
    return _RESICO_BRACKETS[-1].rate


# ---------------------------------------------------------------------------
# RESICO implementation
# ---------------------------------------------------------------------------

class ResicoStrategy:
    def calculate_tax(self, gross_mxn: Decimal) -> TaxResult:
        rate = resolve_bracket(gross_mxn)
        isr = (gross_mxn * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(gross_mxn=gross_mxn, rate=rate, isr=isr, regime_code="RESICO")

    def get_brackets(self) -> list[TaxBracket]:
        return list(_RESICO_BRACKETS[:-1])  # exclude the unbounded sentinel

    def get_regime_code(self) -> str:
        return "RESICO"

    def is_applicable(self, regime_code: str) -> bool:
        return regime_code == "RESICO"


# ---------------------------------------------------------------------------
# Legacy 2% implementation (deprecated)
# ---------------------------------------------------------------------------

class LegacyTaxStrategy:
    def calculate_tax(self, gross_mxn: Decimal) -> TaxResult:
        rate = Decimal("0.02")
        isr = (gross_mxn * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(gross_mxn=gross_mxn, rate=rate, isr=isr, regime_code="LEGACY_2PCT")

    def get_brackets(self) -> list[TaxBracket]:
        return []

    def get_regime_code(self) -> str:
        return "LEGACY_2PCT"

    def is_applicable(self, regime_code: str) -> bool:
        return regime_code == "LEGACY_2PCT"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TaxRegimeRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, TaxRegimeStrategy] = {}

    def register(self, strategy: TaxRegimeStrategy) -> None:
        self._strategies[strategy.get_regime_code()] = strategy

    def resolve(self, regime_code: str) -> TaxRegimeStrategy:
        return self._strategies[regime_code]

    def resolve_all(self) -> dict[str, TaxRegimeStrategy]:
        return dict(self._strategies)


# Default registry with both regimes registered
default_registry = TaxRegimeRegistry()
default_registry.register(ResicoStrategy())
default_registry.register(LegacyTaxStrategy())
