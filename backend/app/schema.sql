-- Conteo schema (SQLite).
-- owner_user_id FK on every owned row; server-side filtering only (ticket 05).

CREATE TABLE IF NOT EXISTS users (
  sub           TEXT PRIMARY KEY,
  email         TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  avatar_url    TEXT,
  language      TEXT NOT NULL,  -- no column default; injected on INSERT
  guide_status  TEXT,
  tax_regime    TEXT NOT NULL DEFAULT 'LEGACY_2PCT',  -- LEGACY_2PCT | RESICO
  created_at    TEXT NOT NULL,
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS bank_settings (
  owner_user_id TEXT PRIMARY KEY REFERENCES users(sub),
  currency      TEXT NOT NULL DEFAULT 'MXN',
  fixed_fee     REAL NOT NULL DEFAULT 320,
  conv_pct      REAL NOT NULL DEFAULT 0,
  tax_pct       REAL NOT NULL DEFAULT 2,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS foreign_clients (
  id              TEXT PRIMARY KEY,
  owner_user_id   TEXT NOT NULL REFERENCES users(sub),
  legal_name      TEXT NOT NULL,
  tax_id          TEXT NOT NULL,             -- foreign tax ID (EIN, etc.)
  rfc             TEXT,                      -- NULL for pure foreign clients
  fiscal_regime   TEXT NOT NULL DEFAULT '616',  -- SAT RegimenFiscal constant
  uso_cfdi        TEXT NOT NULL DEFAULT 'S01',  -- SAT UsoCFDI constant
  country         TEXT NOT NULL DEFAULT 'USA',  -- ISO 3166-1 alpha-3
  currency_option TEXT NOT NULL DEFAULT 'USD',  -- per-client default override
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS income_sources (
  id                TEXT PRIMARY KEY,
  owner_user_id     TEXT NOT NULL REFERENCES users(sub),
  foreign_client_id TEXT REFERENCES foreign_clients(id),
  name              TEXT NOT NULL,
  currency          TEXT NOT NULL,
  fixed_salary      REAL NOT NULL DEFAULT 0,
  commission_mode   TEXT NOT NULL DEFAULT 'none',  -- none | pct | flat
  commission_value  REAL NOT NULL DEFAULT 0,
  active            INTEGER NOT NULL DEFAULT 1,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id             TEXT PRIMARY KEY,
  source_id      TEXT NOT NULL REFERENCES income_sources(id),
  owner_user_id  TEXT NOT NULL REFERENCES users(sub),
  name           TEXT NOT NULL,
  value          REAL NOT NULL,
  assigned       TEXT NOT NULL,   -- ISO date
  est_end        TEXT NOT NULL,   -- ISO date
  approval       TEXT,            -- ISO date or NULL
  settled_month  TEXT,            -- 'YYYY-MM' once paid at a close
  created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settlements (
  id              TEXT PRIMARY KEY,
  source_id       TEXT NOT NULL REFERENCES income_sources(id),
  owner_user_id   TEXT NOT NULL REFERENCES users(sub),
  month           TEXT NOT NULL,           -- 'YYYY-MM'
  typed_mxn       REAL NOT NULL,
  transfers       INTEGER NOT NULL DEFAULT 1,
  fixed_salary_foreign REAL NOT NULL DEFAULT 0,
  commission_foreign   REAL NOT NULL DEFAULT 0,
  foreign_paid    REAL NOT NULL DEFAULT 0,
  gross_mxn       REAL,
  derived_rate    REAL,
  tax             REAL NOT NULL DEFAULT 0,
  net_after_tax   REAL NOT NULL DEFAULT 0,
  paid_project_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array
  commission_breakdown TEXT NOT NULL DEFAULT '[]',  -- JSON [{id,name,commissionForeign}]
  created_at      TEXT NOT NULL,
  UNIQUE (source_id, month)
);

CREATE TABLE IF NOT EXISTS shares (
  id             TEXT PRIMARY KEY,
  owner_user_id  TEXT NOT NULL REFERENCES users(sub),
  sharee_user_id TEXT REFERENCES users(sub),
  pending_email  TEXT,
  source_id      TEXT NOT NULL REFERENCES income_sources(id),
  status         TEXT NOT NULL DEFAULT 'pending',  -- pending | active | dismissed | rejected
  created_at     TEXT NOT NULL,
  updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shares_owner ON shares(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_shares_sharee ON shares(sharee_user_id);

CREATE TABLE IF NOT EXISTS sessions (
  id           TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users(sub),
  created_at   TEXT NOT NULL,
  expires_at   TEXT NOT NULL,
  last_seen_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS auth_tokens (
  user_id            TEXT PRIMARY KEY REFERENCES users(sub),
  google_refresh_token TEXT,
  updated_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_snapshots (
  base       TEXT PRIMARY KEY,
  rates_json TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  source     TEXT NOT NULL,   -- er-api | frankfurter | cached
  stale      INTEGER NOT NULL DEFAULT 0
);

-- CFDI / SAT catalog tables (ticket 04)

CREATE TABLE IF NOT EXISTS sat_product_codes (
  clave           TEXT PRIMARY KEY,
  description     TEXT NOT NULL,
  category        TEXT NOT NULL DEFAULT 'general',
  vigencia_inicio TEXT NOT NULL,
  vigencia_fin    TEXT,            -- NULL = still active
  created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sat_unit_codes (
  clave           TEXT PRIMARY KEY,
  description     TEXT NOT NULL,
  vigencia_inicio TEXT NOT NULL,
  vigencia_fin    TEXT,
  created_at      TEXT NOT NULL
);

-- CFDI invoice tables (tickets 05, 06, 07)

CREATE TABLE IF NOT EXISTS cfdi_invoices (
  id                TEXT PRIMARY KEY,
  owner_user_id     TEXT NOT NULL REFERENCES users(sub),
  source_id         TEXT NOT NULL REFERENCES income_sources(id),
  foreign_client_id TEXT NOT NULL REFERENCES foreign_clients(id),
  month             TEXT NOT NULL,              -- 'YYYY-MM'
  status            TEXT NOT NULL DEFAULT 'draft',  -- draft | stamped | cancelled
  currency_option   TEXT NOT NULL DEFAULT 'USD',    -- USD | MXN
  tipo_comprobante  TEXT NOT NULL DEFAULT 'I',      -- I=ingreso
  metodo_pago       TEXT NOT NULL DEFAULT 'PPD',    -- PUE | PPD
  forma_pago        TEXT NOT NULL DEFAULT '99',     -- 99=Por definir (PPD)
  uso_cfdi          TEXT NOT NULL DEFAULT 'S01',
  serie             TEXT,
  folio             TEXT,
  fecha_emision     TEXT NOT NULL,              -- ISO datetime
  lugar_expedicion  TEXT NOT NULL,              -- 5-digit postal code
  tipo_cambio       REAL,                       -- NULL when Moneda=MXN
  subtotal          REAL NOT NULL DEFAULT 0,
  total             REAL NOT NULL DEFAULT 0,
  iva_rate          REAL NOT NULL DEFAULT 0,    -- 0 for export services
  iva_amount        REAL NOT NULL DEFAULT 0,
  moneda            TEXT NOT NULL DEFAULT 'USD',
  no_certificado    TEXT,                       -- 20-digit CSD serial
  certificado       TEXT,                       -- base64 CSD .cer
  sello             TEXT,                       -- base64 digital seal
  uuid              TEXT,                       -- PAC-assigned UUID (timbre fiscal)
  pac_response      TEXT,                       -- JSON PAC response
  sat_xml           TEXT,                       -- stamped XML from PAC
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  UNIQUE (owner_user_id, source_id, month)
);

CREATE TABLE IF NOT EXISTS cfdi_concepts (
  id              TEXT PRIMARY KEY,
  invoice_id      TEXT NOT NULL REFERENCES cfdi_invoices(id),
  clave_prod_serv TEXT NOT NULL,           -- SAT ClaveProdServ
  clave_unidad    TEXT NOT NULL,           -- SAT ClaveUnidad
  descripcion     TEXT NOT NULL,
  cantidad        REAL NOT NULL DEFAULT 1,
  valor_unitario  REAL NOT NULL,
  importe         REAL NOT NULL,
  objeto_imp      TEXT NOT NULL DEFAULT '01',  -- 01=no objeto, 02=isObjecto
  no_identificacion TEXT,
  created_at      TEXT NOT NULL
);

-- CFDI invoice monthly tax summaries (ticket 08)

CREATE TABLE IF NOT EXISTS monthly_tax_summaries (
  id              TEXT PRIMARY KEY,
  owner_user_id   TEXT NOT NULL REFERENCES users(sub),
  month           TEXT NOT NULL,           -- 'YYYY-MM'
  regime_code     TEXT NOT NULL,           -- RESICO | LEGACY_2PCT
  total_gross_mxn REAL NOT NULL,
  bracket_rate    REAL,                    -- NULL for LEGACY_2PCT
  isr_due         REAL NOT NULL,
  cfdi_count      INTEGER NOT NULL DEFAULT 0,
  breakdown_json  TEXT NOT NULL DEFAULT '[]',  -- JSON array
  status          TEXT NOT NULL DEFAULT 'draft',  -- draft | filed
  generated_at    TEXT NOT NULL,
  filed_at        TEXT,
  UNIQUE (owner_user_id, month)
);
