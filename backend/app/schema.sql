-- Conteo schema (SQLite).
-- owner_user_id FK on every owned row; server-side filtering only (ticket 05).

CREATE TABLE IF NOT EXISTS users (
  sub           TEXT PRIMARY KEY,
  email         TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  avatar_url    TEXT,
  language      TEXT NOT NULL DEFAULT 'en',
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

CREATE TABLE IF NOT EXISTS income_sources (
  id              TEXT PRIMARY KEY,
  owner_user_id   TEXT NOT NULL REFERENCES users(sub),
  name            TEXT NOT NULL,
  currency        TEXT NOT NULL,
  fixed_salary    REAL NOT NULL DEFAULT 0,
  commission_mode TEXT NOT NULL DEFAULT 'none',  -- none | pct | flat
  commission_value REAL NOT NULL DEFAULT 0,
  active          INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
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
