"""Close month — per-source settlement (tickets 01, 02, 04).

One settlement per active source per month, closed when its payment lands. The
user types the exact MXN that hit the bank; the app derives the bank's
effective rate. Which projects actually landed this month is selected at close
(payment selection — approval ≠ payment, carry-over possible).
"""

import json
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import get_db_conn, require_onboarded, require_user
from ..math.settlement import derive
from ..serializers import settlement_dict, source_dict
from ..services.months import MONTH_RE, commission_of, now_iso

router = APIRouter(prefix="/api/close", tags=["close"])


def _source_form(conn, source, bank):
    projects = conn.execute(
        "SELECT * FROM projects WHERE source_id = ? AND settled_month IS NULL ORDER BY created_at",
        (source["id"],),
    ).fetchall()
    return {
        "id": source["id"],
        "name": source["name"],
        "currency": source["currency"],
        "fixedSalary": source["fixed_salary"],
        "commissionMode": source["commission_mode"],
        "commissionValue": source["commission_value"],
        "bankPct": bank["conv_pct"],
        "fixedFee": bank["fixed_fee"],
        "taxPct": bank["tax_pct"],
        "projects": [
            {
                "id": p["id"],
                "name": p["name"],
                "value": p["value"],
                "commissionForeign": commission_of(source, p),
                "approval": p["approval"],
            }
            for p in projects
        ],
    }


@router.get("")
def close_view(
    month: str = Query(...),
    conn: sqlite3.Connection = Depends(get_db_conn),
    bank=Depends(require_onboarded),
    user=Depends(require_user),
):
    if not MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="invalid_month")
    sources = conn.execute(
        "SELECT * FROM income_sources WHERE owner_user_id = ? AND active = 1 ORDER BY created_at",
        (user.sub,),
    ).fetchall()
    settlements = conn.execute(
        "SELECT * FROM settlements WHERE owner_user_id = ? AND month = ?", (user.sub, month)
    ).fetchall()
    settled_ids = {s["source_id"] for s in settlements}
    return {
        "month": month,
        "sources": [_source_form(conn, s, bank) for s in sources if s["id"] not in settled_ids],
        "settlements": [settlement_dict(s) for s in settlements],
    }


class CloseBody(BaseModel):
    month: str
    sourceId: str
    typedMxn: float
    transfers: int = 1
    paidProjectIds: list[str] = []
    # Ticket 02: the salary actually paid that month (sickness/vacation → lower).
    # None = inherit the source's fixed salary.
    fixedSalaryOverride: float | None = None


@router.post("")
def close_month(
    body: CloseBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    bank=Depends(require_onboarded),
    user=Depends(require_user),
):
    if not MONTH_RE.match(body.month):
        raise HTTPException(status_code=422, detail="invalid_month")
    if body.transfers < 1:
        raise HTTPException(status_code=422, detail="invalid_transfers")
    source = conn.execute(
        "SELECT * FROM income_sources WHERE id = ? AND owner_user_id = ?", (body.sourceId, user.sub)
    ).fetchone()
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    if not source["active"]:
        raise HTTPException(status_code=409, detail="source_inactive")
    existing = conn.execute(
        "SELECT id FROM settlements WHERE source_id = ? AND month = ?", (body.sourceId, body.month)
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="month_already_closed")

    paid_ids = set(body.paidProjectIds)
    projects = conn.execute(
        "SELECT * FROM projects WHERE source_id = ? AND owner_user_id = ?", (body.sourceId, user.sub)
    ).fetchall()
    paid_projects = [p for p in projects if p["id"] in paid_ids]
    invalid = paid_ids - {p["id"] for p in paid_projects}
    if invalid:
        raise HTTPException(status_code=422, detail="paid_projects_unknown")

    fixed_foreign = body.fixedSalaryOverride if body.fixedSalaryOverride is not None else source["fixed_salary"]
    commission_foreign = sum(commission_of(source, p) for p in paid_projects)
    foreign_paid = fixed_foreign + commission_foreign

    derived = derive(
        typed_mxn=body.typedMxn,
        foreign_paid=foreign_paid,
        transfers=body.transfers,
        fixed_fee=bank["fixed_fee"],
        conv_pct=bank["conv_pct"],
        tax_pct=bank["tax_pct"],
    )

    settlement_id = "st" + secrets.token_hex(8)
    breakdown = json.dumps(
        [
            {"id": p["id"], "name": p["name"], "commissionForeign": commission_of(source, p)}
            for p in paid_projects
        ]
    )
    conn.execute(
        "INSERT INTO settlements (id, source_id, owner_user_id, month, typed_mxn, transfers, "
        "fixed_salary_foreign, commission_foreign, foreign_paid, gross_mxn, derived_rate, tax, "
        "net_after_tax, paid_project_ids, commission_breakdown, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (settlement_id, body.sourceId, user.sub, body.month, body.typedMxn, body.transfers,
         fixed_foreign, commission_foreign, foreign_paid, derived.gross_mxn, derived.derived_rate,
         derived.tax, derived.net_after_tax, json.dumps(sorted(paid_ids)), breakdown, now_iso()),
    )
    for pid in paid_ids:
        conn.execute("UPDATE projects SET settled_month = ? WHERE id = ? AND owner_user_id = ?",
                     (body.month, pid, user.sub))
    conn.commit()
    row = conn.execute("SELECT * FROM settlements WHERE id = ?", (settlement_id,)).fetchone()
    return settlement_dict(row)