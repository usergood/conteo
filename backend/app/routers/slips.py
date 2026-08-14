"""Salary-slip PDF download (tickets 06, 09, 10).

Owner: any fully-closed month. Sharee: a fully-closed month where they have
an active share on every source contributing to it (the aggregate-slip rule —
ticket 06). Only owners' data is ever read; nothing is copied.
"""

import json
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..auth import get_bank_settings, get_db_conn, require_user
from ..services import slips
from ..services.months import MONTH_RE, fully_closed_months, owner_month_fully_closed

router = APIRouter(prefix="/api/months", tags=["slips"])


def _sections(conn: sqlite3.Connection, owner_id: str, month: str, bank) -> list[dict]:
    settlements = conn.execute(
        "SELECT * FROM settlements WHERE owner_user_id = ? AND month = ? ORDER BY created_at",
        (owner_id, month),
    ).fetchall()
    sections = []
    for st in settlements:
        source = conn.execute("SELECT * FROM income_sources WHERE id = ?", (st["source_id"],)).fetchone()
        rate = st["derived_rate"]
        breakdown = json.loads(st["commission_breakdown"])
        commissions = [
            {
                "name": c["name"],
                "commissionForeign": c["commissionForeign"],
                "commissionMxn": c["commissionForeign"] * rate if rate else None,
            }
            for c in breakdown
        ]
        sections.append({
            "source": source["name"],
            "currency": source["currency"],
            "fixedSalaryForeign": st["fixed_salary_foreign"],
            "fixedMxn": st["fixed_salary_foreign"] * rate if rate else None,
            "commissions": commissions,
            "grossForeign": st["foreign_paid"],
            "grossMxn": st["gross_mxn"],
            "bankPct": bank["conv_pct"],
            "fixedFee": bank["fixed_fee"],
            "transfers": st["transfers"],
            "bankFee": (st["gross_mxn"] - st["typed_mxn"]) if st["gross_mxn"] is not None else None,
            "bankNet": st["typed_mxn"],
            "taxPct": bank["tax_pct"],
            "tax": st["tax"],
            "netAfterTax": st["net_after_tax"],
            "derivedRate": rate,
            "derivedRateLabel": f"{rate:,.4f}" if rate is not None else "—",
        })
    return sections


def _owner_of_month(conn: sqlite3.Connection, month: str) -> str | None:
    row = conn.execute(
        "SELECT owner_user_id FROM settlements WHERE month = ? LIMIT 1", (month,)
    ).fetchone()
    return row["owner_user_id"] if row else None


def _sharee_covers_month(conn: sqlite3.Connection, user_id: str, owner_id: str, month: str) -> bool:
    """Sharee may pull the slip only when the month is fully closed (ticket 06)
    and they hold an active share on every source contributing to it."""
    if not owner_month_fully_closed(conn, owner_id, month):
        return False
    sources = conn.execute(
        "SELECT source_id FROM settlements WHERE owner_user_id = ? AND month = ?", (owner_id, month)
    ).fetchall()
    shared = conn.execute(
        "SELECT source_id FROM shares WHERE owner_user_id = ? AND sharee_user_id = ? AND status = 'active'",
        (owner_id, user_id),
    ).fetchall()
    shared_ids = {row["source_id"] for row in shared}
    return bool(sources) and all(row["source_id"] in shared_ids for row in sources)


@router.get("/{month}/slip")
def slip_pdf(month: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    if not MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="invalid_month")

    bank = get_bank_settings(conn, user.sub)
    if bank is not None and month in fully_closed_months(conn, user.sub):
        view_owner = user.sub
    else:
        candidate_owner = _owner_of_month(conn, month)
        if (
            candidate_owner is None
            or candidate_owner == user.sub
            or not _sharee_covers_month(conn, user.sub, candidate_owner, month)
        ):
            raise HTTPException(status_code=403, detail="no_access")
        view_owner = candidate_owner
        bank = get_bank_settings(conn, view_owner)

    owner_row = conn.execute("SELECT * FROM users WHERE sub = ?", (view_owner,)).fetchone()
    sections = _sections(conn, view_owner, month, bank)
    if not sections:
        raise HTTPException(status_code=404, detail="no_settlements")
    data = slips.build_slip_data(
        month=month,
        user={"displayName": owner_row["display_name"], "email": owner_row["email"]},
        bank={"convPct": bank["conv_pct"], "fixedFee": bank["fixed_fee"], "taxPct": bank["tax_pct"]},
        sections=sections,
        generated=date.today().isoformat(),
    )
    pdf = slips.render_pdf(data)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="salary-slip-{month}.pdf"'},
    )