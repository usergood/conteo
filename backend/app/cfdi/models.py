"""CFDI 4.0 Pydantic models mirroring the official XSD (ticket 05).

Models define the structure; serialization to XML is handled by cfdi_xml.py.
Only the base ``ingreso`` (invoice) CFDI is modeled — complementos like
Nómina / Pagos / Carta Porte are out of scope. The PAC appends the ``tfd``
TimbreFiscalDigital at stamping time.

Sello / Certificado / NoCertificado come from the issuer CSD at signing time
(a separate, PAC-agnostic step via cadena-original XSLT + RSA-SHA256).
They are left empty on the Pydantic model and filled before serialization.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums for SAT catalog values used in the base CFDI
# ---------------------------------------------------------------------------

class TipoDeComprobante(str, Enum):
    INGRESO = "I"
    EGRESO = "E"
    TRASLADO = "T"
    NOMINA = "N"
    PAGO = "P"  # noqa: E501


class MetodoPago(str, Enum):
    PUE = "PUE"
    PPD = "PPD"


class FormaPago(str, Enum):
    EFECTIVO = "01"
    CHEQUE_NOMINATIVO = "02"
    TRANSFERENCIA_ELECTRONICA = "03"
    TARJETA_CREDITO = "04"
    MONEDERO_ELECTRONICO = "05"
    DINERO_ELECTRONICO = "06"
    VALES = "08"
    DACION_EN_PAGO = "12"
    PAGO_POR_CUENTAS_CON_CHEQUE = "13"
    PAGO_EN_ESPECIE = "14"
    POR_DEFINIR = "99"


class Exportacion(str, Enum):
    NO_APLICA = "01"
    DEFINIDO_EN_FISCALIDAD = "02"
    SE_EXPORTA = "03"
    NO_SE_EXPORTA = "04"


class ObjetoImp(str, Enum):
    NO_OBJETO = "01"
    OBJETO = "02"
    NO_APLICA = "03"


class TipoFactor(str, Enum):
    TASA = "Tasa"
    CUOTA = "Cuota"
    EXENTO = "Exento"


class Impuesto(str, Enum):
    IVA = "002"
    ISR = "001"


class Moneda(str, Enum):
    USD = "USD"
    MXN = "MXN"


# ---------------------------------------------------------------------------
# Emisor (issuer)
# ---------------------------------------------------------------------------

class Emisor(BaseModel):
    rfc: str = Field(..., max_length=13, description="RFC del emisor")
    nombre: str = Field(..., max_length=300, description="Nombre o razón social")
    regimen_fiscal: str = Field(..., alias="RegimenFiscal", description="Clave del régimen fiscal")
    fac_atr_adquirente: Optional[str] = Field(None, max_length=10)

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Receptor (receiver / foreign client)
# ---------------------------------------------------------------------------

class Receptor(BaseModel):
    rfc: str = Field(..., description="RFC del receptor (XEXX010101000 for foreign)")
    nombre: str = Field(..., max_length=300)
    domicilio_fiscal_receptor: str = Field(..., max_length=5, description="Código postal")
    residencia_fiscal: Optional[str] = Field(None, max_length=3, description="ISO 3166-1 alpha-3")
    num_reg_id_trib: Optional[str] = Field(None, max_length=40)
    regimen_fiscal_receptor: str = Field(..., alias="RegimenFiscalReceptor")
    uso_cfdi: str = Field(..., alias="UsoCFDI")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Impuestos (taxes)
# ---------------------------------------------------------------------------

class Traslado(BaseModel):
    base: Decimal
    impuesto: str = Field(..., alias="Impuesto")
    tipo_factor: str = Field(..., alias="TipoFactor")
    tasa_o_cuota: Optional[Decimal] = Field(None, alias="TasaOCuota")
    importe: Optional[Decimal] = Field(None, alias="Importe")

    model_config = {"populate_by_name": True}


class ImpuestosTraslados(BaseModel):
    traslado: list[Traslado]


class ImpuestosRetencion(BaseModel):
    base: Decimal
    impuesto: str = Field(..., alias="Impuesto")
    tipo_factor: str = Field(..., alias="TipoFactor")
    tasa_o_cuota: Decimal = Field(..., alias="TasaOCuota")
    importe: Decimal = Field(..., alias="Importe")

    model_config = {"populate_by_name": True}


class ImpuestosConcepto(BaseModel):
    traslados: Optional[ImpuestosTraslados] = None
    retenciones: Optional[list[ImpuestosRetencion]] = None


# ---------------------------------------------------------------------------
# Concepto (line item)
# ---------------------------------------------------------------------------

class Concepto(BaseModel):
    clave_prod_serv: str = Field(..., alias="ClaveProdServ")
    no_identificacion: Optional[str] = Field(None, alias="NoIdentificacion", max_length=100)
    cantidad: Decimal = Field(..., gt=0)
    clave_unidad: str = Field(..., alias="ClaveUnidad")
    unidad: Optional[str] = Field(None, max_length=20)
    descripcion: str = Field(..., max_length=1000)
    valor_unitario: Decimal = Field(..., alias="ValorUnitario", gt=0)
    importe: Decimal = Field(..., gt=0)
    descuento: Optional[Decimal] = Field(None, alias="Descuento")
    objeto_imp: str = Field(..., alias="ObjetoImp")
    impuestos: Optional[ImpuestosConcepto] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Impuestos (comprobante-level tax summary)
# ---------------------------------------------------------------------------

class ImpuestosComprobante(BaseModel):
    total_impuestos_retenidos: Optional[Decimal] = Field(None, alias="TotalImpuestosRetenidos")
    total_impuestos_trasladados: Optional[Decimal] = Field(None, alias="TotalImpuestosTrasladados")
    retenciones: Optional[list[ImpuestosRetencion]] = None
    traslados: Optional[list[Traslado]] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Comprobante (root CFDI element)
# ---------------------------------------------------------------------------

class Comprobante(BaseModel):
    """CFDI 4.0 Comprobante — the root XML element.

    Sello, Certificado and NoCertificado are left empty and filled at signing
    time from the issuer CSD. Version is always "4.0".
    """

    version: str = Field("4.0", alias="Version")
    serie: Optional[str] = Field(None, alias="Serie", max_length=25)
    folio: Optional[str] = Field(None, alias="Folio", max_length=40)
    fecha: str = Field(..., alias="Fecha", description="AAAA-MM-DDThh:mm:ss")
    sello: str = Field("", alias="Sello")
    forma_pago: Optional[str] = Field(None, alias="FormaPago")
    no_certificado: str = Field("", alias="NoCertificado", max_length=20)
    certificado: str = Field("", alias="Certificado")
    condiciones_de_pago: Optional[str] = Field(None, alias="CondicionesDePago", max_length=1000)
    subtotal: Decimal = Field(..., alias="SubTotal")
    descuento: Optional[Decimal] = Field(None, alias="Descuento")
    moneda: str = Field(..., alias="Moneda")
    tipo_cambio: Optional[Decimal] = Field(None, alias="TipoCambio")
    total: Decimal = Field(..., alias="Total")
    tipo_de_comprobante: str = Field(..., alias="TipoDeComprobante")
    exportacion: str = Field("01", alias="Exportacion")
    metodo_pago: Optional[str] = Field(None, alias="MetodoPago")
    lugar_expedicion: str = Field(..., alias="LugarExpedicion", max_length=5)
    confirmacion: Optional[str] = Field(None, alias="Confirmacion", max_length=5)

    emisor: Emisor
    receptor: Receptor
    conceptos: list[Concepto] = Field(..., alias="Conceptos")
    impuestos: Optional[ImpuestosComprobante] = None

    model_config = {"populate_by_name": True}
