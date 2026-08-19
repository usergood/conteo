"""CFDI 4.0 builder — constructs Comprobante from DB data (ticket 05).

Reads income source, foreign client, settlement, and issuer data to build
a complete CFDI 4.0 Comprobante ready for XML serialization and PAC stamping.
"""

from __future__ import annotations

import sqlite3
from decimal import Decimal

from ..services.sat_catalogs import (
    PAIS_USA,
    RFC_GENERICO_EXTRANJERO,
    REGIMEN_FISCAL_EXTRANJERO,
    USO_CFDI_SIN_EFECTOS,
)
from .models import (
    Concepto,
    Comprobante,
    Emisor,
    Receptor,
)


def _dec(val: float | int | str | None, default: str = "0") -> Decimal:
    if val is None:
        return Decimal(default)
    return Decimal(str(val))


class CFDIBuilderError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def build_cfdi(
    conn: sqlite3.Connection,
    *,
    owner_user_id: str,
    source_id: str,
    foreign_client_id: str,
    month: str,
    amount_mxn: Decimal,
    tipo_cambio: Decimal | None = None,
    serie: str | None = None,
    folio: str | None = None,
    fecha: str | None = None,
    moneda: str = "MXN",
    metodo_pago: str = "PUE",
    forma_pago: str = "03",
) -> Comprobante:
    """Build a CFDI 4.0 Comprobante from stored data.

    ``amount_mxn`` is the total invoice amount in the invoiced currency
    (USD for Option A, MXN for Option B). For MXN invoices tipo_cambio
    must be None (omitted from XML). For USD invoices tipo_cambio is required.

    Raises CFDIBuilderError on validation failure.
    """
    fc = conn.execute(
        "SELECT * FROM foreign_clients WHERE id = ? AND owner_user_id = ?",
        (foreign_client_id, owner_user_id),
    ).fetchone()
    if fc is None:
        raise CFDIBuilderError("FOREIGN_CLIENT_NOT_FOUND", "Foreign client not found")

    source = conn.execute(
        "SELECT * FROM income_sources WHERE id = ? AND owner_user_id = ?",
        (source_id, owner_user_id),
    ).fetchone()
    if source is None:
        raise CFDIBuilderError("SOURCE_NOT_FOUND", "Income source not found")

    user = conn.execute("SELECT * FROM users WHERE sub = ?", (owner_user_id,)).fetchone()
    if user is None:
        raise CFDIBuilderError("USER_NOT_FOUND", "Issuer user not found")

    if fecha is None:
        fecha = f"{month}-01T12:00:00"

    concepto = Concepto(
        clave_prod_serv="80101507",  # IT consulting
        clave_unidad="E48",  # Servicio
        descripcion=f"Servicios de consultoría en tecnología de la información - {month}",
        cantidad=Decimal("1"),
        valor_unitario=amount_mxn,
        importe=amount_mxn,
        objeto_imp="01",  # No objeto de impuesto (export services, 0% IVA)
    )

    issuer_rfc = user["issuer_rfc"]
    if not issuer_rfc:
        raise CFDIBuilderError("ISSUER_RFC_MISSING", "Issuer RFC not configured")

    emisor = Emisor(
        rfc=issuer_rfc,
        nombre=user["display_name"],
        regimen_fiscal="621",  # RESICO
    )

    receptor = Receptor(
        rfc=fc["rfc"] or RFC_GENERICO_EXTRANJERO,
        nombre=fc["legal_name"],
        domicilio_fiscal_receptor="00000",
        residencia_fiscal=fc["country"] or PAIS_USA,
        num_reg_id_trib=fc["tax_id"],
        regimen_fiscal_receptor=fc["fiscal_regime"] or REGIMEN_FISCAL_EXTRANJERO,
        uso_cfdi=fc["uso_cfdi"] or USO_CFDI_SIN_EFECTOS,
    )

    comprobante = Comprobante(
        fecha=fecha,
        serie=serie,
        folio=folio,
        forma_pago=forma_pago,
        subtotal=amount_mxn,
        moneda=moneda,
        tipo_cambio=tipo_cambio,
        total=amount_mxn,
        tipo_de_comprobante="I",  # ingreso
        metodo_pago=metodo_pago,
        lugar_expedicion="00000",  # placeholder
        emisor=emisor,
        receptor=receptor,
        conceptos=[concepto],
    )

    return comprobante
