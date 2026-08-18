# Conteo

A multi-user personal-finance app for an IT consultant with customers or employers in different countries: tracks income sources (fixed salary + linked projects, each source in its own currency), forecasts future income months with live FX to MXN, settles months against the exact amount that hits the bank, and produces PDF salary slips for tax season.

## Income & Projects

**Income Source**:
A counterparty that pays income in one currency (e.g. "US company" in USD). Carries an optional fixed salary, a commission mode, an incoming currency, and linked projects. A foreign payer is flagged `is_foreign` and linked to its Foreign Client.
_Avoid_: Employer, client, account

**Fixed Salary**:
The flat monthly amount an income source pays per calendar month, inherited by open salary months until overridden at month close.
_Avoid_: Base pay, monthly salary

**Project**:
A paid engagement linked to one income source. Has a value, an assigned date, an estimated end date (start + 6 weeks, overridable), and an approval date. Inherits its income source's currency.
_Avoid_: Job, engagement, gig

**Commission**:
The income earned per approved project, set per income source either as a percentage of project value or as a fixed amount per project.
_Avoid_: Bonus, cut, percentage

**Approval**:
The customer's acceptance of a project. Approval doesn't equal payment — a project approved in one month may be paid in a later one. The month-close flow selects which unsettled projects were actually paid.
_Avoid_: Sign-off, acceptance, green light

## Months & Money

**Salary Month**:
A calendar month aggregating each source's fixed salary plus commissions from projects selected as paid that month. Holds its own final fixed-salary values. Fully closed only when every active income source that month is closed; closed months are immutable.
_Avoid_: Pay period, pay run

**Settlement**:
The close of a single income source for a month: the user types the bank-net MXN that landed, the app derives the effective FX rate and applies bank fees and tax. One settlement per source per month.
_Avoid_: Close-out, reconciliation, payout

**Bank-Net**:
The exact MXN amount that hits the bank account for a settled income source — the user types this; the app derives the bank's effective rate for that settlement.
_Avoid_: Take-home, net deposit

**Bank Settings**:
Per-user bank/tax configuration collected at account creation — currency, fixed fee, conversion %, tax %. Global per-user (one bank per user, enforced for now); commission % is deliberately not here — it lives per income source.
_Avoid_: Bank account, bank info, tax settings

**Salary Slip**:
The monthly PDF (WeasyPrint HTML/CSS) available once every active source for a month is closed: per-source fixed salary, per-project commission breakdown, conversion + bank fees, tax before/after, net MXN. An internal TAX-friendly record — a CFDI is generated manually in the SAT platform, never by the app.
_Avoid_: Pay stub, invoice, comprobante

**TAX**:
The 2% of bank-net MXN withheld per settlement (setting, global per-user). Slip contents are "TAX-friendly" (the user's term); the formal fiscal document is a CFDI produced outside the app.
_Avoid_: SAT, fiscal document

**Forecast**:
Projected future salary months built from each source's fixed salary plus real assigned projects, converted via live FX.
_Avoid_: Projection, estimate, pipeline

## Sharing

**Share**:
A read-only grant by an income source's owner to another user (by Google email), covering that source's months, settlements, and PDF slips. The sharee sees the source's data only while the share is `active`; sharing never copies or mutates the owner's data.
_Avoid_: Grant, permission, access

---

## CFDI & SAT (Mexican Tax Compliance)

**CFDI 4.0** (*Comprobante Fiscal Digital por Internet*):
The SAT-mandated electronic invoice format (XML + digital seal) for all fiscal transactions in Mexico. Version 4.0 is current.

**PAC** (*Proveedor Autorizado de Certificación*):
SAT-authorized third party that validates, signs, and stamps CFDIs. The app generates unsigned CFDI XML; PAC integration is abstracted behind an interface.

**Tax Regime** (*Régimen Fiscal*):
The issuer's tax classification determining rates and obligations. **RESICO** (*Régimen Simplificado de Confianza*) is the initial regime (1.0–2.5% ISR on gross revenue). The domain model supports multiple regimes via a strategy pattern — not hardcoded.

**Foreign Client** (*ForeignClient*, *Receptor Extranjero*):
A non-Mexican client invoiced via CFDI. Uses generic RFC `XEXX010101000`, fiscal regime `616` (*Sin obligaciones fiscales*), CFDI usage `S01` (*Sin efectos fiscales*), and `0% IVA` under export of services (Art. 29 LIVA). Maps one-to-one to an IncomeSource flagged `is_foreign`; `legal_name` and `tax_id` (EIN) are user-editable while `rfc`, `fiscal_regime`, `uso_cfdi`, and `country` are locked to the foreign-client generics. Carries a `currency_option` default that individual invoices may override.

**Currency Option**:
Two invoicing strategies for USD income:
- **Option A (USD Direct)**: Invoice in USD with Banxico DOF exchange rate (`TipoCambio`); SAT sees MXN equivalence.
- **Option B (MXN Post-Settlement)**: Invoice in MXN for exact bank-net deposited; `Moneda: MXN`, `TipoCambio: 1`. Must be same fiscal month as deposit.

Each Foreign Client stores a `currency_option` default; individual invoices may override it at creation without changing the stored default.

**SAT Product/Service Code** (*ClaveProdServ*):
Catalog code for the invoiced service (e.g., `80101507` IT consultation, `81111508` App development).

**SAT Unit Code** (*ClaveUnidad*):
Catalog code for the unit of measure (e.g., `E48` service unit, `HUR` hours).

**e.firma** (*Firma Electrónica Avanzada*):
The issuer's SAT-issued digital certificate (`.cer`) and private key (`.key` + passphrase) used to sign CFDIs before PAC submission.

**Monthly Tax Workflow**:
Per-calendar-month cycle: ingest payments → generate CFDIs → calculate RESICO ISR by gross MXN brackets → generate pre-filled SAT declaration payload for portal filing → audit trail.

**RESICO ISR Brackets** (monthly gross MXN):
- ≤ 25,000: 1.00%
- ≤ 50,000: 1.10%
- ≤ 83,333: 1.50%
- ≤ 166,666: 2.00%
- ≤ 2,916,666: 2.50%

**Issuer Configuration** (*Configuración del Emisor*):
Pre-configured issuer data: RFC, legal name, fiscal regime, postal code, CSD certificate/key, bank details, tax declaration text. Used as defaults on every CFDI.