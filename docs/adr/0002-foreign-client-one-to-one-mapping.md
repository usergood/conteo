# ADR-0002: IncomeSource ↔ ForeignClient is a one-to-one mapping via a separate table

Status: accepted

## Context

CFDI 4.0 invoicing needs a receptor (`ForeignClient`) for foreign payers, but
the domain's `IncomeSource` is the income counterparty. For foreign payers we
decided one IncomeSource maps to exactly one ForeignClient (a subsidiary is a
distinct payer and should be its own IncomeSource — no N:1). The remaining
question was where the receptor data lives.

## Decision

- **One IncomeSource = one ForeignClient**, enforced by a nullable
  `foreign_client_id` FK on `income_sources`. A source flagged `is_foreign`
  requires it.
- **ForeignClient is a separate `foreign_clients` table**, not fields inlined
  on `income_sources` — it is a distinct entity with its own lifecycle and
  will grow independently (e.g. more countries/regimes later).
- `legal_name` and `tax_id` (EIN) are user-editable; `rfc`
  (`XEXX010101000`), `fiscal_regime` (`616`), `uso_cfdi` (`S01`), and
  `country` (`USA`) are stored but locked to the foreign-client generics.
- **No migration of existing sources**: the database is being wiped and
  rebuilt, so `is_foreign`/`foreign_client_id` start fresh with the new
  schema.

## Considered Options

- **Inline the CFDI fields on `income_sources`** — rejected: couples the
  income domain to the fiscal domain, bloats the source row, and makes the
  future foreign-client growth a schema migration on every source.
- **N:1 or N:N mapping** — rejected: a parent company paying via a subsidiary
  is still a distinct payer; model it as its own IncomeSource.

## Consequences

- The `income_sources` row stays lean; ForeignClient data lives one FK hop
  away for CFDI generation.
- `is_foreign` sources without a linked ForeignClient are blocked from CFDI
  generation until one is attached.