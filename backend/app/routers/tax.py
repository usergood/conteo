"""Monthly tax summary API (ticket 08).

Compute and review monthly ISR by the active tax regime.
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_db_conn, require_user
from ..services.months import MONTH_RE
from ..services.tax_summary import compute_monthly_tax, get_monthly_tax_summary

router = APIRouter(prefix="/api/tax", tags=["tax"])


@router.get("/summary/{month}")
def get_summary(month: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    if not MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="invalid_month")
    summary = get_monthly_tax_summary(conn, user.sub, month)
    if summary is None:
        raise HTTPException(status_code=404, detail="no_summary")
    return summary


@router.post("/summary/{month}/compute")
def compute_summary(month: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    if not MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="invalid_month")
    try:
        summary = compute_monthly_tax(conn, user.sub, month)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
