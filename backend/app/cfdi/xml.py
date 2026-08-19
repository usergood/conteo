"""CFDI 4.0 XML serialization with lxml (ticket 05).

Converts Pydantic Comprobante models to SAT-valid XML. Handles:
- Correct cfdi: namespace prefix
- xsi:schemaLocation with official SAT URLs
- Attribute ordering per XSD specification
- Decimal precision (6 fraction digits per XSD)
"""

from __future__ import annotations

from decimal import Decimal
from lxml import etree

from .models import Comprobante, Concepto, ImpuestosComprobante

# CFDI 4.0 namespaces
CFDI_NS = "http://www.sat.gob.mx/cfd/4"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
CATCFDI_NS = "http://www.sat.gob.mx/sitio_internet/cfd/catalogos"

NSMAP = {
    "cfdi": CFDI_NS,
    "xsi": XSI_NS,
    "catCFDI": CATCFDI_NS,
}

SCHEMA_LOCATION = (
    "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
)


def _fmt_decimal(value: Decimal | None, fraction_digits: int = 6) -> str | None:
    """Format a Decimal to string with fixed fraction digits (no trailing zeros)."""
    if value is None:
        return None
    quantizer = Decimal(10) ** -fraction_digits
    return str(value.quantize(quantizer))


def _add_emisor(elem: etree._Element, comprobante: Comprobante) -> None:
    emisor = etree.SubElement(elem, f"{{{CFDI_NS}}}Emisor")
    emisor.set("Rfc", comprobante.emisor.rfc)
    emisor.set("Nombre", comprobante.emisor.nombre)
    emisor.set("RegimenFiscal", comprobante.emisor.regimen_fiscal)
    if comprobante.emisor.fac_atr_adquirente:
        emisor.set("FacAtrAdquirente", comprobante.emisor.fac_atr_adquirente)


def _add_receptor(elem: etree._Element, comprobante: Comprobante) -> None:
    rec = comprobante.receptor
    receptor = etree.SubElement(elem, f"{{{CFDI_NS}}}Receptor")
    receptor.set("Rfc", rec.rfc)
    receptor.set("Nombre", rec.nombre)
    receptor.set("DomicilioFiscalReceptor", rec.domicilio_fiscal_receptor)
    if rec.residencia_fiscal:
        receptor.set("ResidenciaFiscal", rec.residencia_fiscal)
    if rec.num_reg_id_trib:
        receptor.set("NumRegIdTrib", rec.num_reg_id_trib)
    receptor.set("RegimenFiscalReceptor", rec.regimen_fiscal_receptor)
    receptor.set("UsoCFDI", rec.uso_cfdi)


def _add_concepto_impuestos(parent: etree._Element, concepto: Concepto) -> None:
    if concepto.impuestos is None:
        return
    impuestos_elem = etree.SubElement(parent, f"{{{CFDI_NS}}}Impuestos")
    if concepto.impuestos.traslados:
        traslados = etree.SubElement(impuestos_elem, f"{{{CFDI_NS}}}Traslados")
        for t in concepto.impuestos.traslados.traslado:
            traslado = etree.SubElement(traslados, f"{{{CFDI_NS}}}Traslado")
            traslado.set("Base", _fmt_decimal(t.base))
            traslado.set("Impuesto", t.impuesto)
            traslado.set("TipoFactor", t.tipo_factor)
            if t.tasa_o_cuota is not None:
                traslado.set("TasaOCuota", _fmt_decimal(t.tasa_o_cuota))
            if t.importe is not None:
                traslado.set("Importe", _fmt_decimal(t.importe))


def _add_conceptos(elem: etree._Element, comprobante: Comprobante) -> None:
    conceptos = etree.SubElement(elem, f"{{{CFDI_NS}}}Conceptos")
    for c in comprobante.conceptos:
        concepto = etree.SubElement(conceptos, f"{{{CFDI_NS}}}Concepto")
        concepto.set("ClaveProdServ", c.clave_prod_serv)
        if c.no_identificacion:
            concepto.set("NoIdentificacion", c.no_identificacion)
        concepto.set("Cantidad", _fmt_decimal(c.cantidad))
        concepto.set("ClaveUnidad", c.clave_unidad)
        if c.unidad:
            concepto.set("Unidad", c.unidad)
        concepto.set("Descripcion", c.descripcion)
        concepto.set("ValorUnitario", _fmt_decimal(c.valor_unitario))
        concepto.set("Importe", _fmt_decimal(c.importe))
        if c.descuento is not None:
            concepto.set("Descuento", _fmt_decimal(c.descuento))
        concepto.set("ObjetoImp", c.objeto_imp)
        _add_concepto_impuestos(concepto, c)


def _add_impuestos(elem: etree._Element, impuestos: ImpuestosComprobante) -> None:
    imp = etree.SubElement(elem, f"{{{CFDI_NS}}}Impuestos")
    if impuestos.total_impuestos_retenidos is not None:
        imp.set("TotalImpuestosRetenidos", _fmt_decimal(impuestos.total_impuestos_retenidos))
    if impuestos.total_impuestos_trasladados is not None:
        imp.set("TotalImpuestosTrasladados", _fmt_decimal(impuestos.total_impuestos_trasladados))
    if impuestos.traslados:
        traslados = etree.SubElement(imp, f"{{{CFDI_NS}}}Traslados")
        for t in impuestos.traslados:
            traslado = etree.SubElement(traslados, f"{{{CFDI_NS}}}Traslado")
            traslado.set("Base", _fmt_decimal(t.base))
            traslado.set("Impuesto", t.impuesto)
            traslado.set("TipoFactor", t.tipo_factor)
            if t.tasa_o_cuota is not None:
                traslado.set("TasaOCuota", _fmt_decimal(t.tasa_o_cuota))
            if t.importe is not None:
                traslado.set("Importe", _fmt_decimal(t.importe))


def comprobante_to_xml(comprobante: Comprobante) -> bytes:
    """Serialize a Comprobante to CFDI 4.0 XML bytes.

    The output includes Sello/Certificado/NoCertificado as empty placeholders
    (filled at signing time). Does NOT include the TimbreFiscalDigital
    complement (appended by PAC).
    """
    root = etree.Element(
        f"{{{CFDI_NS}}}Comprobante",
        nsmap=NSMAP,
    )
    root.set(f"{{{XSI_NS}}}schemaLocation", SCHEMA_LOCATION)

    # Comprobante attributes (order per XSD)
    root.set("Version", comprobante.version)
    if comprobante.serie:
        root.set("Serie", comprobante.serie)
    if comprobante.folio:
        root.set("Folio", comprobante.folio)
    root.set("Fecha", comprobante.fecha)
    root.set("Sello", comprobante.sello or "")
    if comprobante.forma_pago:
        root.set("FormaPago", comprobante.forma_pago)
    root.set("NoCertificado", comprobante.no_certificado or "")
    root.set("Certificado", comprobante.certificado or "")
    if comprobante.condiciones_de_pago:
        root.set("CondicionesDePago", comprobante.condiciones_de_pago)
    root.set("SubTotal", _fmt_decimal(comprobante.subtotal))
    if comprobante.descuento is not None:
        root.set("Descuento", _fmt_decimal(comprobante.descuento))
    root.set("Moneda", comprobante.moneda)
    if comprobante.tipo_cambio is not None:
        root.set("TipoCambio", _fmt_decimal(comprobante.tipo_cambio))
    root.set("Total", _fmt_decimal(comprobante.total))
    root.set("TipoDeComprobante", comprobante.tipo_de_comprobante)
    root.set("Exportacion", comprobante.exportacion)
    if comprobante.metodo_pago:
        root.set("MetodoPago", comprobante.metodo_pago)
    root.set("LugarExpedicion", comprobante.lugar_expedicion)
    if comprobante.confirmacion:
        root.set("Confirmacion", comprobante.confirmacion)

    # Child elements
    _add_emisor(root, comprobante)
    _add_receptor(root, comprobante)
    _add_conceptos(root, comprobante)
    if comprobante.impuestos:
        _add_impuestos(root, comprobante.impuestos)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
