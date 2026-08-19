"""Foreign clients CRUD (decision #24).

One IncomeSource = one ForeignClient via a separate `foreign_clients` table + FK.
Locked fields: rfc, fiscal_regime, uso_cfdi, country.
Editable fields: legal_name, tax_id, currency_option.
"""

import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_db_conn, now_iso, require_user

router = APIRouter(prefix="/api/foreign-clients", tags=["foreign-clients"])


def _get_owned_client(conn: sqlite3.Connection, client_id: str, user_id: str):
    row = conn.execute(
        "SELECT * FROM foreign_clients WHERE id = ? AND owner_user_id = ?",
        (client_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="foreign_client_not_found")
    return row


def _client_dict(row) -> dict:
    return {
        "id": row["id"],
        "legalName": row["legal_name"],
        "taxId": row["tax_id"],
        "rfc": row["rfc"],
        "fiscalRegime": row["fiscal_regime"],
        "usoCfdi": row["uso_cfdi"],
        "country": row["country"],
        "currencyOption": row["currency_option"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@router.get("")
def list_foreign_clients(
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    rows = conn.execute(
        "SELECT * FROM foreign_clients WHERE owner_user_id = ? ORDER BY created_at",
        (user.sub,),
    ).fetchall()
    return [_client_dict(r) for r in rows]


class ForeignClientCreateBody(BaseModel):
    legalName: str
    taxId: str
    country: str = "USA"
    currencyOption: str = "USD"


@router.post("")
def create_foreign_client(
    body: ForeignClientCreateBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    if not body.legalName.strip():
        raise HTTPException(status_code=422, detail="legal_name_required")
    if not body.taxId.strip():
        raise HTTPException(status_code=422, detail="tax_id_required")
    if body.currencyOption not in ("USD", "MXN"):
        raise HTTPException(status_code=422, detail="invalid_currency_option")

    client_id = "fc" + secrets.token_hex(8)
    now = now_iso()
    conn.execute(
        "INSERT INTO foreign_clients "
        "(id, owner_user_id, legal_name, tax_id, rfc, fiscal_regime, uso_cfdi, "
        "country, currency_option, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'XEXX010101000', '616', 'S01', ?, ?, ?, ?)",
        (
            client_id, user.sub, body.legalName.strip(), body.taxId.strip(),
            body.country, body.currencyOption, now, now,
        ),
    )
    conn.commit()
    row = _get_owned_client(conn, client_id, user.sub)
    return _client_dict(row)


class ForeignClientUpdateBody(BaseModel):
    legalName: str | None = None
    taxId: str | None = None
    currencyOption: str | None = None


@router.put("/{client_id}")
def update_foreign_client(
    client_id: str,
    body: ForeignClientUpdateBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    _get_owned_client(conn, client_id, user.sub)

    updates = []
    params = []
    if body.legalName is not None:
        if not body.legalName.strip():
            raise HTTPException(status_code=422, detail="legal_name_required")
        updates.append("legal_name = ?")
        params.append(body.legalName.strip())
    if body.taxId is not None:
        if not body.taxId.strip():
            raise HTTPException(status_code=422, detail="tax_id_required")
        updates.append("tax_id = ?")
        params.append(body.taxId.strip())
    if body.currencyOption is not None:
        if body.currencyOption not in ("USD", "MXN"):
            raise HTTPException(status_code=422, detail="invalid_currency_option")
        updates.append("currency_option = ?")
        params.append(body.currencyOption)

    if not updates:
        return _client_dict(_get_owned_client(conn, client_id, user.sub))

    updates.append("updated_at = ?")
    params.append(now_iso())
    params.extend([client_id, user.sub])

    conn.execute(
        f"UPDATE foreign_clients SET {', '.join(updates)} WHERE id = ? AND owner_user_id = ?",
        params,
    )
    conn.commit()
    return _client_dict(_get_owned_client(conn, client_id, user.sub))


@router.get("/{client_id}")
def get_foreign_client(
    client_id: str,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    row = _get_owned_client(conn, client_id, user.sub)
    return _client_dict(row)


@router.delete("/{client_id}")
def delete_foreign_client(
    client_id: str,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    _get_owned_client(conn, client_id, user.sub)

    # Check if linked to any income source
    linked = conn.execute(
        "SELECT COUNT(*) AS n FROM income_sources WHERE foreign_client_id = ? AND owner_user_id = ?",
        (client_id, user.sub),
    ).fetchone()["n"]
    if linked > 0:
        raise HTTPException(status_code=409, detail="foreign_client_in_use")

    conn.execute(
        "DELETE FROM foreign_clients WHERE id = ? AND owner_user_id = ?",
        (client_id, user.sub),
    )
    conn.commit()
    return {"ok": True}
