"""CFDI invoice CRUD + stamping + month-close gate (tickets 05, 06, 07).

One CFDI per foreign client per month. Lifecycle: draft → stamped → cancelled.
Drafts are freely editable; stamped CFDIs change only by PAC cancellation.
CFDI generation is blocked after the source's month is fully closed.

Option A (USD Direct): Generate anytime during the month; PPD if paid later.
Option B (MXN Post-Settlement): Only at settlement time; naturally PUE.
"""

from __future__ import annotations

import json
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_db_conn, require_user
from ..cfdi.builder import CFDIBuilderError, build_cfdi
from ..cfdi.errors import format_pac_error
from ..cfdi.models import Comprobante
from ..cfdi.pac import NullPACProvider, StampResult
from ..cfdi.xml import comprobante_to_xml
from ..services.months import MONTH_RE, now_iso, owner_month_fully_closed
from ..services.sat_catalogs import seed_catalogs, validate_product_code, validate_unit_code

router = APIRouter(prefix="/api/cfdi", tags=["cfdi"])

# Default PAC provider (null for dev/test)
_default_pac = NullPACProvider()


def _get_owned_invoice(conn: sqlite3.Connection, invoice_id: str, user_id: str):
    row = conn.execute(
        "SELECT * FROM cfdi_invoices WHERE id = ? AND owner_user_id = ?",
        (invoice_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="invoice_not_found")
    return row


class InvoiceCreateBody(BaseModel):
    sourceId: str
    foreignClientId: str
    month: str
    currencyOption: str = "USD"
    amountMxn: float
    tipoCambio: float | None = None
    serie: str | None = None
    folio: str | None = None


class InvoiceUpdateBody(BaseModel):
    amountMxn: float | None = None
    tipoCambio: float | None = None
    serie: str | None = None
    folio: str | None = None
    currencyOption: str | None = None


def _invoice_dict(row) -> dict:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "foreignClientId": row["foreign_client_id"],
        "month": row["month"],
        "status": row["status"],
        "currencyOption": row["currency_option"],
        "metodoPago": row["metodo_pago"],
        "formaPago": row["forma_pago"],
        "usoCfdi": row["uso_cfdi"],
        "serie": row["serie"],
        "folio": row["folio"],
        "fechaEmision": row["fecha_emision"],
        "subtotal": row["subtotal"],
        "total": row["total"],
        "moneda": row["moneda"],
        "tipoCambio": row["tipo_cambio"],
        "uuid": row["uuid"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@router.get("/invoices")
def list_invoices(
    month: str | None = None,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    if month and not MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="invalid_month")
    if month:
        rows = conn.execute(
            "SELECT * FROM cfdi_invoices WHERE owner_user_id = ? AND month = ? ORDER BY created_at",
            (user.sub, month),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM cfdi_invoices WHERE owner_user_id = ? ORDER BY created_at DESC",
            (user.sub,),
        ).fetchall()
    return [_invoice_dict(r) for r in rows]


@router.post("/invoices")
def create_invoice(
    body: InvoiceCreateBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    if not MONTH_RE.match(body.month):
        raise HTTPException(status_code=422, detail="invalid_month")
    if body.currencyOption not in ("USD", "MXN"):
        raise HTTPException(status_code=422, detail="invalid_currency_option")
    if body.amountMxn <= 0:
        raise HTTPException(status_code=422, detail="amount_must_be_positive")

    # Verify foreign client belongs to user
    fc = conn.execute(
        "SELECT id FROM foreign_clients WHERE id = ? AND owner_user_id = ?",
        (body.foreignClientId, user.sub),
    ).fetchone()
    if fc is None:
        raise HTTPException(status_code=404, detail="foreign_client_not_found")

    # Verify source belongs to user and is linked to the foreign client
    source = conn.execute(
        "SELECT id FROM income_sources WHERE id = ? AND owner_user_id = ? AND foreign_client_id = ?",
        (body.sourceId, user.sub, body.foreignClientId),
    ).fetchone()
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    # Month-close gate: cannot create CFDI after month is fully closed
    if owner_month_fully_closed(conn, user.sub, body.month):
        raise HTTPException(status_code=409, detail="month_already_closed")

    # Check no duplicate for same (source, month)
    existing = conn.execute(
        "SELECT id FROM cfdi_invoices WHERE owner_user_id = ? AND source_id = ? AND month = ?",
        (user.sub, body.sourceId, body.month),
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="invoice_already_exists_for_source_month")

    # Determine payment method
    if body.currencyOption == "USD":
        metodo_pago = "PPD"
        forma_pago = "99"  # Por definir
        moneda = "USD"
    else:
        metodo_pago = "PUE"
        forma_pago = "03"  # Transferencia electrónica
        moneda = "MXN"

    invoice_id = "cf" + secrets.token_hex(8)
    now = now_iso()
    fecha_emision = f"{body.month}-01T12:00:00"

    conn.execute(
        "INSERT INTO cfdi_invoices "
        "(id, owner_user_id, source_id, foreign_client_id, month, status, "
        "currency_option, metodo_pago, forma_pago, uso_cfdi, serie, folio, "
        "fecha_emision, lugar_expedicion, tipo_cambio, subtotal, total, "
        "moneda, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, 'S01', ?, ?, ?, '00000', ?, ?, ?, ?, ?, ?)",
        (
            invoice_id, user.sub, body.sourceId, body.foreignClientId, body.month,
            body.currencyOption, metodo_pago, forma_pago,
            body.serie, body.folio, fecha_emision,
            body.tipoCambio, body.amountMxn, body.amountMxn, moneda,
            now, now,
        ),
    )
    conn.commit()
    row = _get_owned_invoice(conn, invoice_id, user.sub)
    return _invoice_dict(row)


@router.put("/invoices/{invoice_id}")
def update_invoice(
    invoice_id: str,
    body: InvoiceUpdateBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    inv = _get_owned_invoice(conn, invoice_id, user.sub)
    if inv["status"] != "draft":
        raise HTTPException(status_code=409, detail="can_only_edit_drafts")

    updates = []
    params = []
    if body.amountMxn is not None:
        if body.amountMxn <= 0:
            raise HTTPException(status_code=422, detail="amount_must_be_positive")
        updates.extend(["subtotal = ?", "total = ?"])
        params.extend([body.amountMxn, body.amountMxn])
    if body.tipoCambio is not None:
        updates.append("tipo_cambio = ?")
        params.append(body.tipoCambio)
    if body.serie is not None:
        updates.append("serie = ?")
        params.append(body.serie)
    if body.folio is not None:
        updates.append("folio = ?")
        params.append(body.folio)
    if body.currencyOption is not None:
        if body.currencyOption not in ("USD", "MXN"):
            raise HTTPException(status_code=422, detail="invalid_currency_option")
        updates.append("currency_option = ?")
        params.append(body.currencyOption)

    if not updates:
        return _invoice_dict(inv)

    updates.append("updated_at = ?")
    params.append(now_iso())
    params.extend([invoice_id, user.sub])

    conn.execute(
        f"UPDATE cfdi_invoices SET {', '.join(updates)} WHERE id = ? AND owner_user_id = ?",
        params,
    )
    conn.commit()
    return _invoice_dict(_get_owned_invoice(conn, invoice_id, user.sub))


@router.post("/invoices/{invoice_id}/preview")
def preview_invoice(
    invoice_id: str,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    """Preview the CFDI XML without stamping (read-only)."""
    inv = _get_owned_invoice(conn, invoice_id, user.sub)

    try:
        comprobante = build_cfdi(
            conn,
            owner_user_id=user.sub,
            source_id=inv["source_id"],
            foreign_client_id=inv["foreign_client_id"],
            month=inv["month"],
            amount_mxn=__import__("decimal").Decimal(str(inv["total"])),
            tipo_cambio=__import__("decimal").Decimal(str(inv["tipo_cambio"])) if inv["tipo_cambio"] else None,
            serie=inv["serie"],
            folio=inv["folio"],
            moneda=inv["moneda"],
            metodo_pago=inv["metodo_pago"],
            forma_pago=inv["forma_pago"],
        )
        xml_bytes = comprobante_to_xml(comprobante)
        return {"xml": xml_bytes.decode("utf-8")}
    except CFDIBuilderError as e:
        raise HTTPException(status_code=422, detail=e.code)


@router.post("/invoices/{invoice_id}/stamp")
def stamp_invoice(
    invoice_id: str,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    """Stamp a draft CFDI through the PAC."""
    inv = _get_owned_invoice(conn, invoice_id, user.sub)
    if inv["status"] != "draft":
        raise HTTPException(status_code=409, detail="can_only_stamp_drafts")

    # Month-close gate
    if owner_month_fully_closed(conn, user.sub, inv["month"]):
        raise HTTPException(status_code=409, detail="month_already_closed")

    try:
        from decimal import Decimal as D
        comprobante = build_cfdi(
            conn,
            owner_user_id=user.sub,
            source_id=inv["source_id"],
            foreign_client_id=inv["foreign_client_id"],
            month=inv["month"],
            amount_mxn=D(str(inv["total"])),
            tipo_cambio=D(str(inv["tipo_cambio"])) if inv["tipo_cambio"] else None,
            serie=inv["serie"],
            folio=inv["folio"],
            moneda=inv["moneda"],
            metodo_pago=inv["metodo_pago"],
            forma_pago=inv["forma_pago"],
        )
        xml_bytes = comprobante_to_xml(comprobante)

        # Stamp through PAC
        result: StampResult = _default_pac.stamp(xml_bytes.decode("utf-8"))

        now = now_iso()
        conn.execute(
            "UPDATE cfdi_invoices SET status = 'stamped', uuid = ?, "
            "sat_xml = ?, pac_response = ?, updated_at = ? "
            "WHERE id = ? AND owner_user_id = ?",
            (result.uuid, result.sat_xml, json.dumps(result.pac_response), now,
             invoice_id, user.sub),
        )
        conn.commit()
        return _invoice_dict(_get_owned_invoice(conn, invoice_id, user.sub))
    except CFDIBuilderError as e:
        raise HTTPException(status_code=422, detail=e.code)


@router.delete("/invoices/{invoice_id}")
def cancel_invoice(
    invoice_id: str,
    conn: sqlite3.Connection = Depends(get_db_conn),
    user=Depends(require_user),
):
    """Cancel a stamped CFDI (through PAC) or delete a draft."""
    inv = _get_owned_invoice(conn, invoice_id, user.sub)

    if inv["status"] == "draft":
        conn.execute(
            "DELETE FROM cfdi_concepts WHERE invoice_id = ?", (invoice_id,)
        )
        conn.execute(
            "DELETE FROM cfdi_invoices WHERE id = ? AND owner_user_id = ?",
            (invoice_id, user.sub),
        )
        conn.commit()
        return {"ok": True, "action": "deleted"}

    if inv["status"] == "stamped":
        if inv["uuid"] is None:
            raise HTTPException(status_code=409, detail="no_uuid_to_cancel")
        result = _default_pac.cancel(inv["uuid"], "01")
        now = now_iso()
        conn.execute(
            "UPDATE cfdi_invoices SET status = 'cancelled', "
            "pac_response = json_patch(pac_response, ?), updated_at = ? "
            "WHERE id = ? AND owner_user_id = ?",
            (json.dumps({"cancellation": result.pac_response}), now,
             invoice_id, user.sub),
        )
        conn.commit()
        return _invoice_dict(_get_owned_invoice(conn, invoice_id, user.sub))

    raise HTTPException(status_code=409, detail="invoice_already_cancelled")
