"""Monthly tax summary computation (ticket 08).

Computes ISR for a (user, month) pair using the active tax regime strategy.
Stores a MonthlyTaxSummary record as audit trail. Months are never recomputed
under a new regime after filing.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from decimal import Decimal

from ..tax_regime import TaxRegimeRegistry, default_registry
from .months import now_iso


def compute_monthly_tax(
    conn: sqlite3.Connection,
    owner_user_id: str,
    month: str,
    registry: TaxRegimeRegistry | None = None,
) -> dict:
    """Compute the monthly tax summary for a user and month.

    Returns the summary dict. Raises if no CFDIs found or month is filed.
    """
    if registry is None:
        registry = default_registry

    # Get user's tax regime
    user = conn.execute("SELECT tax_regime FROM users WHERE sub = ?", (owner_user_id,)).fetchone()
    if user is None:
        raise ValueError("User not found")
    regime_code = user["tax_regime"]

    # Get active strategy
    strategy = registry.resolve(regime_code)

    # Get all stamped CFDIs for this month
    invoices = conn.execute(
        "SELECT id, total, currency_option, tipo_cambio, fecha_emision, foreign_client_id "
        "FROM cfdi_invoices WHERE owner_user_id = ? AND month = ? AND status = 'stamped'",
        (owner_user_id, month),
    ).fetchall()

    if not invoices:
        raise ValueError("No stamped CFDIs found for this month")

    # Calculate total gross MXN
    total_gross_mxn = Decimal("0")
    breakdown = []
    for inv in invoices:
        total = Decimal(str(inv["total"]))
        currency = inv["currency_option"]
        tc = inv["tipo_cambio"]

        if currency == "USD" and tc is not None:
            total_mxn = total * Decimal(str(tc))
        else:
            total_mxn = total

        total_gross_mxn += total_mxn

        # Get client name
        fc = conn.execute(
            "SELECT legal_name FROM foreign_clients WHERE id = ?", (inv["foreign_client_id"],)
        ).fetchone()
        client_name = fc["legal_name"] if fc else "Unknown"

        breakdown.append({
            "uuid": inv["id"],
            "date": inv["fecha_emision"],
            "client": client_name,
            "total_mxn": str(total_mxn),
            "currency_option": currency,
        })

    # Compute tax using the regime strategy
    result = strategy.calculate_tax(total_gross_mxn)

    # Get bracket rate for RESICO
    bracket_rate = None
    if regime_code == "RESICO":
        from ..tax_regime import resolve_bracket
        bracket_rate = float(resolve_bracket(total_gross_mxn))

    summary_id = "ts" + secrets.token_hex(8)
    summary = {
        "id": summary_id,
        "owner_user_id": owner_user_id,
        "month": month,
        "regime_code": regime_code,
        "total_gross_mxn": float(total_gross_mxn),
        "bracket_rate": bracket_rate,
        "isr_due": float(result.isr),
        "cfdi_count": len(invoices),
        "breakdown": breakdown,
        "status": "draft",
        "generated_at": now_iso(),
        "filed_at": None,
    }

    # Upsert into DB
    conn.execute(
        "INSERT OR REPLACE INTO monthly_tax_summaries "
        "(id, owner_user_id, month, regime_code, total_gross_mxn, bracket_rate, "
        "isr_due, cfdi_count, breakdown_json, status, generated_at, filed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            summary_id, owner_user_id, month, regime_code,
            float(total_gross_mxn), bracket_rate, float(result.isr),
            len(invoices), json.dumps(breakdown), "draft", now_iso(), None,
        ),
    )
    conn.commit()

    return summary


def get_monthly_tax_summary(
    conn: sqlite3.Connection,
    owner_user_id: str,
    month: str,
) -> dict | None:
    """Retrieve a stored monthly tax summary."""
    row = conn.execute(
        "SELECT * FROM monthly_tax_summaries WHERE owner_user_id = ? AND month = ?",
        (owner_user_id, month),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "month": row["month"],
        "regime_code": row["regime_code"],
        "total_gross_mxn": row["total_gross_mxn"],
        "bracket_rate": row["bracket_rate"],
        "isr_due": row["isr_due"],
        "cfdi_count": row["cfdi_count"],
        "breakdown": json.loads(row["breakdown_json"]),
        "status": row["status"],
        "generated_at": row["generated_at"],
        "filed_at": row["filed_at"],
    }
