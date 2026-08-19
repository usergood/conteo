"""SQLite connection + schema init. SQLite is a single-file DB (ticket 07)."""

import sqlite3
from pathlib import Path

from .config import get_settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: str) -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    migrate_guide_status(conn)
    migrate_tax_regime(conn)
    migrate_issuer_rfc(conn)
    _seed_sat_catalogs(conn)


def migrate_guide_status(conn: sqlite3.Connection) -> None:
    """Guarded, idempotent migration: add users.guide_status if missing and
    backfill it. New users default to 'pending' (set explicitly on INSERT in
    auth._upsert_user); existing users are backfilled based on their data:
      - 'done'   where a bank_settings row exists (existing onboarded users)
      - 'pending' otherwise (so the guide can open for them too)
    Safe to run on a DB that already has the column.
    """
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "guide_status" in cols:
        # Column already present (fresh DB via schema.sql, or previously migrated).
        # Only backfill NULL rows — never override an explicit skipped/done choice.
        conn.execute(
            "UPDATE users SET guide_status = 'done' WHERE guide_status IS NULL AND sub IN "
            "(SELECT owner_user_id FROM bank_settings)"
        )
        conn.execute("UPDATE users SET guide_status = 'pending' WHERE guide_status IS NULL")
        conn.commit()
        return
    conn.execute("ALTER TABLE users ADD COLUMN guide_status TEXT")
    conn.execute(
        "UPDATE users SET guide_status = 'done' WHERE sub IN (SELECT owner_user_id FROM bank_settings)"
    )
    conn.execute("UPDATE users SET guide_status = 'pending' WHERE guide_status IS NULL")
    conn.commit()


def migrate_tax_regime(conn: sqlite3.Connection) -> None:
    """Guarded, idempotent migration: add users.tax_regime if missing and
    backfill existing users to LEGACY_2PCT. New users get the column default
    from schema.sql. Safe to run on a DB that already has the column."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "tax_regime" in cols:
        conn.execute("UPDATE users SET tax_regime = 'LEGACY_2PCT' WHERE tax_regime IS NULL")
        conn.commit()
        return
    conn.execute("ALTER TABLE users ADD COLUMN tax_regime TEXT NOT NULL DEFAULT 'LEGACY_2PCT'")
    conn.execute("UPDATE users SET tax_regime = 'LEGACY_2PCT' WHERE tax_regime IS NULL")
    conn.commit()


def default_db_path() -> str:
    settings = get_settings()
    return str(Path(settings.data_dir) / "conteo.db")


def _seed_sat_catalogs(conn: sqlite3.Connection) -> None:
    """Seed SAT catalog tables if empty (ticket 04). Idempotent."""
    from .services.sat_catalogs import seed_catalogs
    row = conn.execute("SELECT COUNT(*) AS n FROM sat_product_codes").fetchone()
    if row["n"] == 0:
        seed_catalogs(conn)


def migrate_issuer_rfc(conn: sqlite3.Connection) -> None:
    """Guarded, idempotent migration: add users.issuer_rfc if missing.
    The issuer RFC is the user's SAT-registered RFC for signing CFDIs."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "issuer_rfc" in cols:
        return
    conn.execute("ALTER TABLE users ADD COLUMN issuer_rfc TEXT")
    conn.commit()
