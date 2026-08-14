"""Forecast — per-view calculation, never stored (ticket 04).

Window: `window` months from the first not-fully-closed month (current month
included), extended to include any unsettled project's estimated end. Fixed
salary lands every active month; unsettled projects land by estimated end
(overdue ones carry forward into the first month); approved-but-unpaid
projects stay expected until paid at a close. One FX snapshot for the whole
window, cross-derived from the USD snapshot.
"""

from fastapi import APIRouter, Depends, Query
import sqlite3

from ..auth import get_db_conn, require_onboarded, require_user
from ..math.forecast import build
from ..services import fx
from ..services.months import add_months, commission_of, current_month_key, fully_closed_months, source_active_in

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


def _landing_month(project, start: str) -> str:
    month = project["est_end"][:7]
    return month if month >= start else start


def _serialize_row(row, source, projects, commissions_by_project):
    return {
        "sourceId": source["id"],
        "sourceName": source["name"],
        "currency": source["currency"],
        "grossForeign": row.gross_foreign,
        "rateMxn": row.rate_mxn,
        "rateStale": row.rate_stale,
        "grossMxn": row.gross_mxn,
        "bankNet": row.bank_net,
        "netAfterTax": row.net_after_tax,
        "projects": [
            {"id": p["id"], "name": p["name"], "value": p["value"],
             "commissionForeign": commissions_by_project[p["id"]], "estEnd": p["est_end"]}
            for p in projects
        ],
    }


def build_forecast(conn: sqlite3.Connection, user_id: str, window: int, bank) -> dict:
    sources = conn.execute(
        "SELECT * FROM income_sources WHERE owner_user_id = ? AND active = 1 ORDER BY created_at",
        (user_id,),
    ).fetchall()
    projects = conn.execute(
        "SELECT * FROM projects WHERE owner_user_id = ? AND settled_month IS NULL ORDER BY created_at",
        (user_id,),
    ).fetchall()

    cur = current_month_key()
    closed = set(fully_closed_months(conn, user_id))
    start = cur if cur not in closed else add_months(cur, 1)

    end = add_months(start, max(1, window) - 1)
    for p in projects:
        m = _landing_month(p, start)
        if m > end:
            end = m  # a project past the window extends the horizon

    months = []
    m = start
    while m <= end:
        active = [s for s in sources if source_active_in(s["created_at"], m)]
        landing_by_source: dict = {}
        commissions_by_project: dict = {}
        for s in active:
            landing = [p for p in projects if p["source_id"] == s["id"] and _landing_month(p, start) == m]
            landing_by_source[s["id"]] = landing
            for p in landing:
                commissions_by_project[p["id"]] = commission_of(s, p)
        rows = []
        for s in active:
            landing = landing_by_source[s["id"]]
            fixed = s["fixed_salary"]
            commissions = sum(commissions_by_project[p["id"]] for p in landing)
            # A present but cached-fallback rate still converts and is flagged;
            # only a missing/48h-old rate (mxn_per → None) drops to own-currency.
            rate, stale = fx.mxn_per(conn, s["currency"])
            rows.append({
                "source_id": s["id"],
                "source_name": s["name"],
                "currency": s["currency"],
                "gross_foreign": fixed + commissions,
                "rate_mxn": rate,
                "rate_stale": stale,
            })
        forecast = build(rows, fixed_fee=bank["fixed_fee"], conv_pct=bank["conv_pct"], tax_pct=bank["tax_pct"])
        serialized = [
            _serialize_row(r, s, landing_by_source[s["id"]], commissions_by_project)
            for r, s in zip(forecast.rows, active)
        ]
        months.append({
            "month": m,
            "rows": serialized,
            "totals": {
                "grossMxn": forecast.totals.gross_mxn,
                "bankNet": forecast.totals.bank_net,
                "netAfterTax": forecast.totals.net_after_tax,
            },
        })
        m = add_months(m, 1)
    return {"windowStart": start, "windowEnd": end, "months": months}


@router.get("")
def forecast(
    window: int = Query(default=3, ge=1, le=24),
    conn: sqlite3.Connection = Depends(get_db_conn),
    bank=Depends(require_onboarded),
    user=Depends(require_user),
):
    return build_forecast(conn, user.sub, window, bank)