# 10 - Last fog: slip status, slip layout & onboarding flow

Type: grilling
Status: resolved
Blocked by: 01, 02, 04, 05, 07, 09

## Question

Graduate the map's remaining "Not yet specified" fog, now that every blocking ticket is resolved:

1. **PDF salary-slip status & TAX-facing contents** — is the slip a formal Mexican fiscal document (CFDI de nómina) or an internal record? What does it carry?
2. **Slip layout** — the field-by-field structure of the monthly PDF.
3. **First-login / onboarding flow** — reconcile 05 ("zero income sources → empty state, no onboarding flag") with 07 ("bank settings collected at account creation, before any income source").

The *transfer structure* fog item was ticket 01's job and resolved there (`rate = (typed_MXN + transfers × fixed_fee) ÷ (USD_paid × (1 − bank%))`); no further decision needed.

## Notes / context

- 01: slip shows bank-net vs bank-net−tax side by side; 02: one slip per fully-closed month (all sources closed); 09: WeasyPrint + Jinja2 HTML/CSS, 2 decimals, peso as `$` + `MXN`.

## Comments

- **Q1 (slip status)** — internal record, not a CFDI. The CFDI is generated manually in the SAT platform; no integration planned. Call it **TAX**-friendly, not SAT-friendly.
- **Q2 (slip layout)** — agreed as recommended: one slip per fully-closed month; header (app name, month, user name/email, generated date); one section per income source (fixed salary source-currency gross → MXN, per-project commission breakdown table, gross source-currency total → MXN at that settlement's derived FX rate, bank fee = conversion % + fixed fee, bank-net MXN typed value, tax 2% of bank-net, net-after-tax MXN); totals across sources at foot, per-source derived rates listed, "internal record, not a CFDI" note.
- **Q3 (onboarding flow)** — agreed as recommended: new user = no `bank_settings` row (data-detection, no flag, per 05's spirit). First sign-in → required bank-settings step (currency MXN, fixed fee 320, conversion %, tax 2%, pre-filled) → then the "Add your first income source" empty state. A user with settings but no sources sees the plain empty state. Settings editable later on a Settings page.

## Answer

All three fog items resolved as agreed in comments. Fog graduated; glossary extended (`Salary Slip`, `TAX`, `Bank Settings`) in `CONTEXT.md`; self-setup guide written at `README.md`. Nothing structural remains undecided — the map is a complete spec and implementation is the next phase.