"""Bank settings + language + guide status (tickets 03, 07, 10, 11)."""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_db_conn, now_iso, require_user
from ..config import seed_defaults
from ..serializers import bank_dict

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/seed")
def seed():
    return seed_defaults()


class BankBody(BaseModel):
    fixedFee: float
    convPct: float
    taxPct: float


@router.put("/bank")
def save_bank(body: BankBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    now = now_iso()
    conn.execute(
        "INSERT INTO bank_settings (owner_user_id, currency, fixed_fee, conv_pct, tax_pct, created_at, updated_at) "
        "VALUES (?, 'MXN', ?, ?, ?, ?, ?) "
        "ON CONFLICT(owner_user_id) DO UPDATE SET fixed_fee = excluded.fixed_fee, "
        "conv_pct = excluded.conv_pct, tax_pct = excluded.tax_pct, updated_at = excluded.updated_at",
        (user.sub, body.fixedFee, body.convPct, body.taxPct, now, now),
    )
    conn.commit()
    row = conn.execute(
        "SELECT currency, fixed_fee, conv_pct, tax_pct FROM bank_settings WHERE owner_user_id = ?",
        (user.sub,),
    ).fetchone()
    return bank_dict(row)


class LanguageBody(BaseModel):
    language: str


@router.put("/language")
def save_language(body: LanguageBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    lang = body.language if body.language in ("en", "es") else "en"
    conn.execute("UPDATE users SET language = ? WHERE sub = ?", (lang, user.sub))
    conn.commit()
    return {"language": lang}


class GuideStatusBody(BaseModel):
    guideStatus: str


@router.put("/guide-status")
def save_guide_status(body: GuideStatusBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    status = body.guideStatus
    if status not in ("skipped", "done"):
        raise HTTPException(status_code=422, detail="guideStatus must be 'skipped' or 'done'")
    # 'pending' cannot be set through the API — the guide only ever moves the
    # flag forward to skipped/done; pending is reserved for new users.
    conn.execute("UPDATE users SET guide_status = ? WHERE sub = ?", (status, user.sub))
    conn.commit()
    row = conn.execute("SELECT guide_status FROM users WHERE sub = ?", (user.sub,)).fetchone()
    return {"guideStatus": row["guide_status"]}
