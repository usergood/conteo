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
A calendar month aggregating each source's fixed salary plus commissions from projects selected as paid that month. Holds its own final fixed-salary values. Fully closed only when every active income source that month is closed; closed months are immutable. "Close" means **end of receiving** for that month, not end of the calendar month — once closed, no CFDI may ever be issued for it again (the CFDI set is frozen; taxes for that month are computed from that frozen set).
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
The default fixed-rate tax handling, now the **LEGACY_2PCT** tax regime: 2% (a per-user setting) of bank-net MXN withheld per settlement. Slip contents are "TAX-friendly" (the user's term); the formal fiscal document is a CFDI produced outside the app.
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

**CFDI Generation**:
The app builds the unsigned-but-issuer-signed CFDI XML itself (PAC-agnostic) using hand-rolled **Pydantic models** mirroring CFDI 4.0, serialized with `lxml`; `satcfdi` is kept only as a test *reference oracle*, not a runtime dependency. CI gates on XSD validation (`cfdv40.xsd` plus mirrored `catCFDI.xsd` + `tdCFDI.xsd`). Only the base `ingreso` CFDI is generated — complementos like Nómina/Pagos/Carta Porte are out of scope, and the PAC appends the `tfd` TimbreFiscalDigital at stamping. Namespaces use the `cfdi:` prefix with the required `xsi:schemaLocation`; `Sello`/`Certificado`/`NoCertificado` come from the issuer CSD at signing time (a separate, PAC-agnostic step via cadena-original XSLT + RSA-SHA256). Golden XML fixtures guard regression.

**Tax Regime** (*Régimen Fiscal*):
The issuer's tax classification determining rates and obligations. **RESICO** (*Régimen Simplificado de Confianza*) is the initial regime (1.0–2.5% ISR on gross revenue, bracket-based); **LEGACY_2PCT** is the app's default fixed-rate handling (2% of bank-net MXN). Multiple regimes are supported via a **strategy pattern** — not hardcoded. Each user has exactly one active tax regime, chosen when configuring their bank: `LEGACY_2PCT` is the default, `RESICO` is opted into; there is no feature flag. Regime codes are app-level (`RESICO`, `LEGACY_2PCT`); the SAT's own `RegimenFiscal` claves (e.g. `621` for RESICO) are a separate concern resolved at CFDI generation.
_Avoid_: 2% TAX as the only tax model

**Foreign Client** (*ForeignClient*, *Receptor Extranjero*):
A non-Mexican client invoiced via CFDI. Uses generic RFC `XEXX010101000`, fiscal regime `616` (*Sin obligaciones fiscales*), CFDI usage `S01` (*Sin efectos fiscales*), and `0% IVA` under export of services (Art. 29 LIVA). Maps one-to-one to an IncomeSource flagged `is_foreign`; `legal_name` and `tax_id` (EIN) are user-editable while `rfc`, `fiscal_regime`, `uso_cfdi`, and `country` are locked to the foreign-client generics. Carries a `currency_option` default that individual invoices may override.

**Currency Option**:
Two invoicing strategies for USD income:
- **Option A (USD Direct)**: Invoice in USD with Banxico DOF exchange rate (`TipoCambio`); SAT sees MXN equivalence. Issued at service completion in the source's month; if payment lands in a later month it is issued as **PPD** (MetodoPago PPD, FormaPago 99 "Por definir") and a **Complemento de Pago** receipt is emitted when payment arrives.
- **Option B (MXN Post-Settlement)**: Invoice in MXN for exact bank-net deposited; `Moneda: MXN`, `TipoCambio: 1`. Must be same fiscal month as deposit — naturally **PUE** (payment received in the same month as issuance).

Each Foreign Client stores a `currency_option` default; individual invoices may override it at creation without changing the stored default.

**CFDI Invoice** (*Factura CFDI*):
One CFDI 4.0 invoice per foreign client per month, generated from a source-month. Carries its own lifecycle (draft → stamped → cancelled): drafts are freely editable, a stamped CFDI changes only by PAC cancellation + fresh generation, and corrections are allowed until the month closes. Issuance is gated per source: it must precede the source's month-close.
_Avoid_: Comprobante, recibo, slip

**Complemento de Pago** (*Recibo Electrónico de Pago*, REP):
The SAT-required payment receipt complement issued when a PPD CFDI's payment actually arrives — within the 5th natural day of the month after the payment month (RMF 2026 2.7.1.32). The income CFDI is issued at operation time; the REP records each payment received against it.

**SAT Product/Service Code** (*ClaveProdServ*):
Catalog code for the invoiced service (e.g., `80101507` IT consultation, `81111508` App development).

**SAT Unit Code** (*ClaveUnidad*):
Catalog code for the unit of measure (e.g., `E48` service unit, `HUR` hours).

**SAT Catalog**:
The official SAT code lists a CFDI line item draws from: `ClaveProdServ`, `ClaveUnidad`, plus fixed constants `UsoCFDI` (`S01`), `Pais` (`USA`, alpha-3 string), `RegimenFiscal` (`616`), `Moneda` (`USD`/`MXN`), `FormaPago` (`03`). Stored in `sat_product_codes` + `sat_unit_codes` tables, seeded with a curated IT/consulting subset (~22 product, ~12 unit codes); other catalogs are hard-seeded constants with no admin UI. Versioned via `vigencia_inicio`/`vigencia_fin` (active = fin null or >= today); deprecated codes are never hard-deleted so historical CFDIs stay referenceable. CFDI generation *hard-validates* each code exists and is active, rejecting generation otherwise. Seeded manually via migration in v1; an optional later uploader syncs the community `phpcfdi`/`bambucode` mirror.

**e.firma** (*Firma Electrónica Avanzada*):
The issuer's SAT-issued digital certificate (`.cer`) and private key (`.key` + passphrase) used to sign CFDIs before PAC submission.

**Monthly Tax Workflow**:
Per-calendar-month cycle: ingest payments → generate CFDIs → calculate ISR by the active tax regime (RESICO by gross MXN brackets, LEGACY_2PCT by fixed rate) → generate pre-filled SAT declaration payload for portal filing → audit trail.

**Monthly Tax Summary**:
The stored record of one month's tax computation per user: period, total gross MXN, applicable bracket and rate, ISR due, CFDI count, per-CFDI breakdown, and the **tax regime** that computed it (audit trail). Recomputable while the month's CFDIs can still change; once the month is closed or filed, it is history — past months are never recomputed under a new regime.

**RESICO ISR Brackets** (monthly gross MXN):
- ≤ 25,000: 1.00%
- ≤ 50,000: 1.10%
- ≤ 83,333: 1.50%
- ≤ 166,666: 2.00%
- ≤ 2,916,666: 2.50%

**Issuer Configuration** (*Configuración del Emisor*):
Pre-configured per-user issuer data: RFC, legal name, fiscal regime, postal code, CSD certificate/key, bank details, tax declaration text. Used as defaults on every CFDI. Strictly scoped per user (accessed only within the owner's scope), consistent with the per-user `Bank Settings` and `Share` model.

**CSD Encryption** (*Cifrado de CSD*):
The issuer's e.firma CSD is persisted encrypted at rest (AES-256-GCM) under a key derived from *two* secrets — the app's master key (secret store) and the issuer's e.firma passphrase — so neither the app alone nor a leaked database can decrypt it. The passphrase is the single e.firma password: it both derives the storage key and unlocks the private key at signing, is supplied only to open an in-memory stamping session, and is never persisted (zeroized at session end). See ADR-0003.