"""SAT catalog codes — seed data + validation (ticket 04).

Curated subset of SAT ClaveProdServ and ClaveUnidad for IT/consulting services.
Codes are versioned via vigencia_inicio / vigencia_fin; deprecated codes stay
in the DB so historical CFDIs remain referenceable. CFDI generation hard-validates
that each code exists and is active.
"""

import sqlite3
from datetime import date

# ---------------------------------------------------------------------------
# Seed data — curated IT/consulting subset
# ---------------------------------------------------------------------------

PRODUCT_CODES: list[tuple[str, str, str]] = [
    ("80101507", "Servicios de consultoría en tecnología de la información", "consulting"),
    ("81111508", "Desarrollo de software a la medida", "development"),
    ("81111506", "Servicios de mantenimiento de software", "maintenance"),
    ("81111505", "Servicios de integración de sistemas de información", "integration"),
    ("81111511", "Servicios de soporte técnico de tecnologías de la información", "support"),
    ("81111513", "Servicios de administración de bases de datos", "database"),
    ("81111514", "Servicios de seguridad de la información", "security"),
    ("81111515", "Servicios de nube (cloud computing)", "cloud"),
    ("80101503", "Servicios de auditoría en tecnología de la información", "audit"),
    ("80101504", "Servicios de capacitación en tecnología de la información", "training"),
    ("80101505", "Servicios de planeación en tecnología de la información", "planning"),
    ("80101506", "Servicios de arquitectura de tecnología de la información", "architecture"),
    ("81111501", "Servicios de programación", "programming"),
    ("81111502", "Servicios de pruebas de software", "testing"),
    ("81111503", "Servicios de documentación técnica", "documentation"),
    ("81111504", "Servicios de diseño de software", "design"),
    ("81111510", "Servicios de migración de datos", "migration"),
    ("81111512", "Servicios de análisis de datos", "analytics"),
    ("43232300", "Software de aplicación", "software"),
    ("80101600", "Servicios de gestión empresarial", "management"),
    ("81112200", "Servicios de telecommunications", "telecom"),
    ("82101500", "Servicios de publicidad", "advertising"),
]

UNIT_CODES: list[tuple[str, str]] = [
    ("E48", "Servicio"),
    ("HUR", "Hora"),
    ("DAY", "Día"),
    ("MON", "Mes"),
    ("WK", "Semana"),
    ("SMI", "Quincena"),
    ("YR", "Año"),
    ("ACT", "Actividad"),
    ("BX", "Caja"),
    ("KGM", "Kilogramo"),
    ("MTR", "Metro"),
    ("LTR", "Litro"),
]

# Fixed SAT constants (no admin UI needed)
MONEDA_USD = "USD"
MONEDA_MXN = "MXN"
REGIMEN_FISCAL_EXTRANJERO = "616"
USO_CFDI_SIN_EFECTOS = "S01"
PAIS_USA = "USA"
RFC_GENERICO_EXTRANJERO = "XEXX010101000"


def seed_catalogs(conn: sqlite3.Connection) -> None:
    """Insert curated seed data. Idempotent — skips existing keys."""
    now = date.today().isoformat()
    for clave, desc, cat in PRODUCT_CODES:
        conn.execute(
            "INSERT OR IGNORE INTO sat_product_codes "
            "(clave, description, category, vigencia_inicio, created_at) VALUES (?, ?, ?, ?, ?)",
            (clave, desc, cat, now, now),
        )
    for clave, desc in UNIT_CODES:
        conn.execute(
            "INSERT OR IGNORE INTO sat_unit_codes "
            "(clave, description, vigencia_inicio, created_at) VALUES (?, ?, ?, ?)",
            (clave, desc, now, now),
        )
    conn.commit()


def validate_product_code(conn: sqlite3.Connection, clave: str) -> bool:
    """True if the code exists and is currently active."""
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT 1 FROM sat_product_codes WHERE clave = ? "
        "AND vigencia_inicio <= ? AND (vigencia_fin IS NULL OR vigencia_fin >= ?)",
        (clave, today, today),
    ).fetchone()
    return row is not None


def validate_unit_code(conn: sqlite3.Connection, clave: str) -> bool:
    """True if the code exists and is currently active."""
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT 1 FROM sat_unit_codes WHERE clave = ? "
        "AND vigencia_inicio <= ? AND (vigencia_fin IS NULL OR vigencia_fin >= ?)",
        (clave, today, today),
    ).fetchone()
    return row is not None


def list_product_codes(conn: sqlite3.Connection, active_only: bool = True) -> list[dict]:
    today = date.today().isoformat()
    if active_only:
        rows = conn.execute(
            "SELECT clave, description, category FROM sat_product_codes "
            "WHERE vigencia_inicio <= ? AND (vigencia_fin IS NULL OR vigencia_fin >= ?) "
            "ORDER BY clave",
            (today, today),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT clave, description, category, vigencia_fin FROM sat_product_codes ORDER BY clave"
        ).fetchall()
    return [dict(r) for r in rows]


def list_unit_codes(conn: sqlite3.Connection, active_only: bool = True) -> list[dict]:
    today = date.today().isoformat()
    if active_only:
        rows = conn.execute(
            "SELECT clave, description FROM sat_unit_codes "
            "WHERE vigencia_inicio <= ? AND (vigencia_fin IS NULL OR vigencia_fin >= ?) "
            "ORDER BY clave",
            (today, today),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT clave, description, vigencia_fin FROM sat_unit_codes ORDER BY clave"
        ).fetchall()
    return [dict(r) for r in rows]
