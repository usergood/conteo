"""Tests for CFDI 4.0 models and XML serialization (ticket 05)."""

from decimal import Decimal

import pytest

from app.cfdi.models import (
    Comprobante,
    Concepto,
    Emisor,
    ImpuestosComprobante,
    Receptor,
    Traslado,
)
from app.cfdi.xml import comprobante_to_xml, _fmt_decimal


class TestFmtDecimal:
    def test_basic(self):
        assert _fmt_decimal(Decimal("1234.567890")) == "1234.567890"

    def test_none(self):
        assert _fmt_decimal(None) is None

    def test_integer(self):
        assert _fmt_decimal(Decimal("100")) == "100.000000"

    def test_small_value(self):
        assert _fmt_decimal(Decimal("0.01")) == "0.010000"

    def test_zero(self):
        assert _fmt_decimal(Decimal("0")) == "0.000000"


def _minimal_comprobante() -> Comprobante:
    """Build a minimal valid Comprobante for testing."""
    return Comprobante(
        fecha="2026-01-15T12:00:00",
        subtotal=Decimal("5000.00"),
        total=Decimal("5000.00"),
        moneda="USD",
        tipo_cambio=Decimal("17.500000"),
        tipo_de_comprobante="I",
        metodo_pago="PPD",
        forma_pago="99",
        lugar_expedicion="06600",
        emisor=Emisor(
            rfc="XEXX010101000",
            nombre="Test Issuer",
            regimen_fiscal="621",
        ),
        receptor=Receptor(
            rfc="XEXX010101000",
            nombre="Test Client",
            domicilio_fiscal_receptor="00000",
            residencia_fiscal="USA",
            num_reg_id_trib="12-3456789",
            regimen_fiscal_receptor="616",
            uso_cfdi="S01",
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="80101507",
                clave_unidad="E48",
                descripcion="IT consulting services",
                cantidad=Decimal("1"),
                valor_unitario=Decimal("5000.00"),
                importe=Decimal("5000.00"),
                objeto_imp="01",
            ),
        ],
    )


class TestComprobanteModel:
    def test_minimal_construction(self):
        c = _minimal_comprobante()
        assert c.version == "4.0"
        assert c.fecha == "2026-01-15T12:00:00"
        assert c.subtotal == Decimal("5000.00")
        assert c.total == Decimal("5000.00")
        assert c.moneda == "USD"
        assert c.tipo_cambio == Decimal("17.500000")

    def test_emisor(self):
        c = _minimal_comprobante()
        assert c.emisor.rfc == "XEXX010101000"
        assert c.emisor.nombre == "Test Issuer"
        assert c.emisor.regimen_fiscal == "621"

    def test_receptor(self):
        c = _minimal_comprobante()
        assert c.receptor.rfc == "XEXX010101000"
        assert c.receptor.uso_cfdi == "S01"

    def test_concepto(self):
        c = _minimal_comprobante()
        assert len(c.conceptos) == 1
        assert c.conceptos[0].clave_prod_serv == "80101507"


class TestXMLSerialization:
    def test_produces_valid_xml(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"<?xml" in xml_bytes
        assert b"Comprobante" in xml_bytes
        assert b"4.0" in xml_bytes

    def test_namespaces(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"http://www.sat.gob.mx/cfd/4" in xml_bytes
        assert b"schemaLocation" in xml_bytes

    def test_emisor_in_xml(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"Emisor" in xml_bytes
        assert b"XEXX010101000" in xml_bytes
        assert b"621" in xml_bytes

    def test_receptor_in_xml(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"Receptor" in xml_bytes
        assert b"S01" in xml_bytes
        assert b"616" in xml_bytes

    def test_conceptos_in_xml(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"Conceptos" in xml_bytes
        assert b"80101507" in xml_bytes
        assert b"E48" in xml_bytes

    def test_decimal_formatting(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b"5000.000000" in xml_bytes

    def test_usd_tipo_cambio(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b'TipoCambio="17.500000"' in xml_bytes

    def test_mxn_no_tipo_cambio(self):
        c = _minimal_comprobante()
        c.moneda = "MXN"
        c.tipo_cambio = None
        xml_bytes = comprobante_to_xml(c)
        assert b"TipoCambio" not in xml_bytes

    def test_optional_serie_folio(self):
        c = _minimal_comprobante()
        c.serie = "A"
        c.folio = "1234"
        xml_bytes = comprobante_to_xml(c)
        assert b'Serie="A"' in xml_bytes
        assert b'Folio="1234"' in xml_bytes

    def test_empty_sello_placeholder(self):
        c = _minimal_comprobante()
        xml_bytes = comprobante_to_xml(c)
        assert b'Sello=""' in xml_bytes
        assert b'NoCertificado=""' in xml_bytes

    def test_with_tax_traslado(self):
        c = _minimal_comprobante()
        c.impuestos = ImpuestosComprobante(
            total_impuestos_trasladados=Decimal("0.00"),
            traslados=[
                Traslado(
                    base=Decimal("5000.00"),
                    impuesto="002",
                    tipo_factor="Exento",
                ),
            ],
        )
        xml_bytes = comprobante_to_xml(c)
        assert b"Impuestos" in xml_bytes
        assert b"Traslados" in xml_bytes
        assert b"Exento" in xml_bytes

    def test_encoding_is_utf8(self):
        c = _minimal_comprobante()
        c.receptor.nombre = "Café Corporation"
        xml_bytes = comprobante_to_xml(c)
        assert xml_bytes.startswith(b"<?xml version='1.0' encoding='UTF-8'?>")
