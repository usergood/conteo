# Conteo — UX Design Brief for open-design.ai

> Complete system structure + information needs for a new UI design. Covers what is **already built** and every **new CFDI/SAT feature not yet implemented** (so the design can accommodate them from day one).

---

## 1. What the product is

**Conteo** is a personal-finance app for a Mexico-based IT consultant (RESICO tax regime) who has clients/employers in different countries. It tracks income sources (fixed salary + project commissions, each in its own currency), forecasts future months with live FX, settles each month against the exact amount that hits the bank, and produces PDF salary slips.

**New scope (in design, not built):** the app will also generate Mexican **CFDI 4.0 electronic invoices** (SAT-compliant), track the monthly **RESICO tax** on gross MXN, and produce a pre-filled monthly **SAT declaration** the user files manually on the SAT portal.

**Users:** a single primary user (the contractor). Secondary: family members given read-only access to selected income sources ("shares"). Multi-user with strict per-user data separation.

**Languages:** English + Spanish (in-app switch). **Themes:** light + dark.

---

## 2. Global app shell (existing)

- **App bar:** logo + app name, current user email, transient notice toasts, install button (PWA), language selector, theme toggle, logout.
- **Sidebar/bottom navigation** with 6 entries, each an emoji + label:
  📈 Forecast · 🏢 Sources · 💰 Close Month · 🗓️ Months · 🔗 Share · ⚙️ Settings
- **New nav entries will be needed** for the CFDI/SAT features (see §5).
- **Splash screen** while the app hydrates (logo + loading dots + version).

---

## 3. Existing screens — fields & behavior (built)

### 3.1 Login
- Google Sign-In button (primary auth). Dev-login fallback (token + email) in dev builds.

### 3.2 Onboarding setup guide (3-step overlay, auto-opens for new users)
1. **Bank settings** — currency (MXN default), fixed fee (default 320), conversion % (default 0), tax % (default 2).
2. **Income source** — unlocks once bank settings saved.
3. **Project** — unlocks once a source exists.
- Overlay dialog; no outside-click close. Buttons: Skip all, Finish (available from step 2).

### 3.3 Settings (screen)
- Same **Bank settings** form: currency, fixed fee, conversion %, tax %.
- "Open setup guide" action.
- **New (planned):** issuer fiscal configuration, tax regime, CSD certificate management — see §5.

### 3.4 Sources (screen) — list of income sources
Each source card shows:
- **Name**, **currency** tag (e.g. USD), inactive badge if deactivated
- **Fixed salary** (or "no fixed salary"), **commission mode** (none / % / flat per project)
- **Project count**
- Edit button. Empty state with CTA.

**Source form (add/edit) fields:**
- Name
- Currency (picker from ~166 supported currencies, e.g. USD, SEK, MXN)
- Fixed salary
- Commission mode: none | percentage | flat amount
- Commission value (when mode ≠ none)

### 3.5 Source detail — Projects (screen)
Source header (name, currency, edit, deactivate; delete only when inactive and empty).
- **Project cards:** name, value (in source currency), assigned date, est. end date, approval date (approved/not badge), commission computed in source currency + approximate MXN, edit/delete.
- **Project form fields:** name, value, assigned date, estimated end date (auto = assigned + 6 weeks), approval date (optional).

### 3.6 Forecast (screen)
- Month window selector (3 / 6 / 12 months), current month highlighted.
- Per month, per source row: source name, currency, **gross in source currency**, **gross MXN**, **bank-net MXN** (after conversion % + fixed fee), **net after tax** (after tax %). Stale-rate warning badge.
- Collapsible "advanced": formula breakdown (fixed + commissions, project list feeding it, FX rate used).
- Per-month totals: bank-net total, net-after-tax total.
- Empty states: no sources yet / no data.

### 3.7 Close Month (screen) — the per-source settlement flow
- Month picker (defaults to current month).
- **Per source** (one panel each, collapsible):
  - Project checkboxes — select which projects were **actually paid** this month (approved-in-month projects are pre-checked but still dese-lectable; approval ≠ payment).
  - Fixed salary display + **override field** (sick leave etc.).
  - **Transfers** count.
  - **Typed bank-net MXN** — the exact amount that hit the bank.
  - **Live preview:** derived FX rate, gross MXN, net MXN, tax, net-after-tax.
  - "Close" button per source.
- Section listing already-settled sources for the month.
- When every active source is settled: "All done" state. **Closing a month is final** — after close the month is immutable and can never be re-invoiced.

### 3.8 Months (screen) — closed months
- Tabs: **Mine** / **Shared**.
- Filters: search text, year, month, source.
- Table (Mine): month label, source count + names, gross by currency, bank-net, tax, **"Slip" PDF link**.
- Table (Shared): month, owner, source, gross foreign, bank-net, tax, slip link.
- Slip = downloadable PDF salary slip for a fully-closed month.

### 3.9 Share (screen) — read-only access grants
- Create share: pick a source + sharee Google email.
- **By me:** list of shares with status (pending / active / dismissed / rejected), revoke.
- **With me:** incoming shares, dismiss / undismiss.
- Sharee sees only that source's months + slips while active.

---

## 4. Data model — the information the app holds

### User
`sub` (id) · email · display name · avatar URL · language (en/es) · guide status (pending/skipped/done)

### Bank settings (per user, one row)
currency (MXN default) · fixed fee (320) · conversion % (0) · tax % (2)

### Income source
id · name · currency · fixed salary · commission mode (none/pct/flat) · commission value · active
**New:** `is_foreign` (bool) · `foreign_client_id` (nullable FK)

### Foreign client — **NEW (not built)**
One-to-one with a foreign income source. Fields:
- **legal name** (editable)
- **tax ID / EIN** (editable, optional)
- **RFC** — locked to `XEXX010101000` (generic foreign)
- **fiscal regime** — locked to `616`
- **UsoCFDI** — locked to `S01`
- **country** — locked to `USA`
- **currency option** — `USD_DIRECT` | `MXN_POST_SETTLEMENT` (default USD_DIRECT); overridable per invoice

### Project
id · name · value · assigned date · estimated end date · approval date · settled month (set once paid)

### Settlement (one per source per month)
source · month · typed bank-net MXN · transfers · fixed salary foreign · commission foreign · foreign paid · gross MXN · derived rate · tax · net after tax · paid project ids · commission breakdown

### Share
source · sharee email · status (pending/active/dismissed/rejected)

### CFDI invoice — **NEW (not built)**
One per (source, month). Status lifecycle **draft → stamped → cancelled**.
id · source · month · status · stamped UUID · optional settlement link · currency option used · amounts · SAT product/unit codes per line · XML

### Issuer configuration — **NEW (not built)**
Per-user SAT issuer data used as defaults on every CFDI:
- RFC · legal name · fiscal regime · postal code
- CSD certificate (`.cer`) + private key (`.key`) + passphrase (encrypted at rest)
- Bank details · tax declaration text

### SAT catalogs — **NEW (not built)**
- Product/service codes (ClaveProdServ) — curated IT/consulting subset (~22)
- Unit codes (ClaveUnidad) — subset (~12)
- Locked constants: UsoCFDI `S01`, country `USA`, regime `616`, currencies USD/MXN, FormaPago `03`

### Monthly tax summary — **NEW (not built)**
Per user per month: period · total gross MXN (sum of stamped CFDIs) · applicable RESICO bracket · rate · ISR due · CFDI count · per-CFDI breakdown · regime code used · generated-at

### FX snapshot (existing)
base USD · rates map · fetched-at · source · stale flag

---

## 5. New CFDI & SAT features — UX requirements (NOT built)

> Design must leave room for these. Feature-flagged, opt-in. Domestic clients, payroll/nómina, and physical goods are **out of scope**.

### 5.1 Monthly tax workflow (the mental model the whole feature follows)
Per calendar month:
1. **Receive/record payments** (existing Close Month flow)
2. **Generate CFDIs** for the month
3. **Calculate RESICO ISR** on gross MXN (bracketed: ≤25k=1.0%, ≤50k=1.1%, ≤83,333=1.5%, ≤166,666=2.0%, ≤2,916,666=2.5%)
4. **Review + pre-fill** the SAT declaration (manual portal filing; no SAT API)
5. **Audit trail** of everything

Key rule: a month **closes** = end of receiving for that month. Once closed, **never invoice it again**; its CFDI set is frozen and taxes are computed from it. Taxes for month M are done in M+1 (declaration due by the 17th).

### 5.2 Foreign client management (NEW screen or section)
Attach to each foreign income source. Fields as in §4 Foreign client. UX affordances:
- Create/edit form: legal name, EIN, currency option (USD Direct / MXN Post-Settlement)
- Locked SAT fields (RFC, regime, UsoCFDI, country) shown as **read-only reference values**, not editable
- The client's currency option is the **default** for its invoices; each invoice may override it

### 5.3 Invoicing / CFDI screen (NEW)
Per (source, month), one CFDI. Entry points: from the source's month, or from the Close Month flow.
- **List of invoices** with status badge (draft / stamped / cancelled), UUID when stamped, amounts.
- **Option A (USD Direct):** invoice in USD using the official **Banxico FIX rate** (`TipoCambio`) for the invoice date. May be issued during the month (even before payment). Amount = fixed salary + commissions of projects paid that month.
- **Option B (MXN Post-Settlement):** invoice in MXN for the **exact bank-net deposited**; `TipoCambio: 1`. Only possible at/after settlement; must stay in the same fiscal month as the deposit.
- **Cross-month (Option A):** if the payment lands in a later month, the invoice is issued as **PPD** (FormaPago 99 "Por definir") at service completion, and a **Complemento de Pago** receipt is emitted when the payment arrives (within 5th natural day of the month after payment).
- **Preview before stamping:** review screen showing the pre-filled CFDI fields side-by-side with the SAT reference data; approve → stamp via PAC.
- **Edit window:** unstamped drafts freely editable; a stamped CFDI changes only by **cancellation + re-generation**; all corrections allowed until the month closes.

### 5.4 PAC stamping (integrated behind the scenes, minimal UI)
- Action: "Stamp" on a draft → sends XML to the PAC → returns the stamped UUID/TimbreFiscalDigital.
- **Cancel** a stamped CFDI (needs a reason; PAC `cancel`).
- Status query per UUID.
- Errors surface through the friendly mapping (§5.6).

### 5.5 e.firma / CSD credentials (NEW settings section)
- Upload `.cer` certificate + `.key` private key + passphrase (once per session, or persisted encrypted at rest).
- **Encrypted storage; never logged; passphrase held in memory only.**
- **Certificate expiry tracking:** alert at 30 / 15 / 7 days before expiry; block stamping once expired.
- Strict per-user isolation. This is high-security, careful UI (password-style fields, warnings).

### 5.6 SAT/PAC error handling (NEW UX pattern)
- Backend maps raw PAC/SAT codes (e.g. duplicate UUID, expired certificate, invalid seal) to a friendly message + **remediation steps**.
- Frontend: error banner/toast with the friendly message, a "Learn more" link, and a **remediation checklist**.
- Config-driven, extensible without deploys.

### 5.7 Monthly tax declaration review (NEW screen)
- Period selector (default: previous month).
- Summary: total gross MXN, applicable bracket + rate, **ISR due**, CFDI count.
- **Per-CFDI breakdown:** UUID, date, client, MXN total.
- **Editable pre-filled fields** (user can adjust before filing).
- **Copy to clipboard** per field + "Copy all" — designed for manual entry into the SAT portal.
- **Export artifacts:** JSON / PDF / CSV.
- **Audit trail:** every generated summary stored (regime code used, generated-at).
- Regenerate allowed while CFDIs can still change (before filing).

### 5.8 Tax regime (NEW, low-UI)
- User assigned to a tax regime: `RESICO` (new) or `LEGACY_2PCT` (existing 2% TAX).
- New users: RESICO opt-in; existing users stay legacy until they opt in.
- The regime drives which tax math applies; the Monthly Tax Summary records which was used.

---

## 6. Design considerations / constraints

- **Numbers are the product:** currencies, rates, MXN amounts everywhere. Both the source currency and MXN matter — show both, label clearly (e.g. `$ 5,000 USD` and `$ 85,000 MXN`). Thousands separators, 2–4 decimals where relevant.
- **Fiscal correctness is non-negotiable:** the UI should *prevent* SAT-invalid states (locked foreign-client generics, no non-zero IVA on exports, no Option B outside the deposit month, no invoicing a closed month).
- **Manual portal entry is a first-class flow:** the app pre-fills reference data the user *types into the SAT portal* — so "copy" affordances, side-by-side reference views, and review-before-submit are core patterns.
- **Feature-flagged:** the CFDI/SAT features are opt-in; the existing 2% TAX flow stays untouched for legacy users.
- **States everywhere:** draft/stamped/cancelled (CFDI), pending/active/dismissed/rejected (shares), closed vs open (months), pending/skipped/done (guide). Use status badges consistently.
- **Empty states** matter: new user, no sources, no projects, no settled months, no invoices yet.
- **Small screen + PWA:** installable, works well on mobile.
- **Trust & care:** fiscal documents, certificates, passwords — the design should feel precise, trustworthy, calm (banking-adjacent), not playful.