# Wayfinder map: Salary tracker & forecaster

## Destination

A complete specification for a multi-user salary tracker & forecaster — enough that later sessions implement it end-to-end: income sources (fixed salary + linked projects, each source in its own currency), live-FX forecasting to MXN, bank-settlement math at month close, read-only sharing between Google users, and PDF salary slips.

## Notes

- **Domain**: personal finance for a contractor in Mexico City paid into CitiBancoMex. Fixed salary (2500 USD/mo default) + 8% commission per approved project. Projects: $18k–$80k USD, manual entry, 2–6 weeks, up to 3 concurrent, paid on customer approval.
- **Skills**: HITL tickets via `/grilling` + `/domain-modeling`. Research tickets via `/research` subagents (AFK).
- **Stack (user's brief)**: Python FastAPI backend, Next.js/React frontend (mobile-friendly), SQLite storage, Docker with config + db mounted outside the container.
- **Auth**: Google Sign-In only. **Deploy**: self-hosted behind Cloudflare Tunnel, likely `https://salary.glappet.eu`.
- **Currency**: everything reports to MXN. Bank: fixed fee 320 MXN/transfer (default), static % on conversion, both settings. Tax: 2% of bank-net MXN, PDF shows before/after.
- **Standing preferences**: user types exact MXN that hits the account at month close; app derives the bank's effective rate. Real assigned projects drive the forecast (estimated end = start + 6 weeks, overridable); no assumed pipeline.
- Refer to tickets **by name**, never by bare number, in narration and in Decisions-so-far.

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [Decide global vs per-income-source settings](issues/03-settings-scope.md) — settings scope: bank fixed fee, bank conversion %, tax %, bank currency all **global per-user** (one bank per user is an enforced limit for now); **commission % is per income source, default 0** (both fields 0 = no income per project); changes forward-only (closed settlements immutable). Per-user bank/tax settings row holds currency, fixed fee, conversion %, tax % — commission % drops out of it (ripples to 07's config.yaml seeds). Unblocks 04.
- [Last fog: slip status, slip layout & onboarding flow](issues/10-last-fog-slip-and-onboarding.md) — **Slip status**: the monthly PDF is an **internal record**, not a CFDI — the CFDI is generated manually in the SAT platform, no integration planned. TAX-friendly contents, not SAT (per user: "call it TAX instead of SAT"). **Slip layout** (agreed as recommended): one slip per fully-closed month; header (app name, month, user name/email, generated date); one section per income source (fixed salary source-currency gross → MXN, per-project commission breakdown table, gross source-currency total → MXN at that settlement's derived FX rate, bank fee = conversion % + fixed fee, bank-net MXN typed value, tax 2% of bank-net, net-after-tax MXN); totals across sources at foot, per-source derived rates listed, "internal record, not a CFDI" note. **Onboarding flow**: new user = no `bank_settings` row (data-detection, no flag per 05); first sign-in → required bank-settings step (currency MXN, fixed fee 320, conversion %, tax 2%, pre-filled) → then "Add your first income source" empty state; user with settings but no sources sees plain empty state; settings editable later on a Settings page.
- [Research live FX data sources](issues/08-research-fx-source.md) — Use open.er-api.com (no key, hourly poll; 24h refresh); fallback Frankfurter v2 then cached snapshot.
- [Research PDF generation for salary slips](issues/09-research-pdf-lib.md) — WeasyPrint + Jinja2 (HTML/CSS templates, Docker-friendly); ReportLab runner-up.
- [Pick the deployment + Cloudflare Tunnel shape](issues/07-deployment-shape.md) — single container (Next.js standalone + FastAPI + SQLite); one hostname `salary.glappet.eu` → one origin, cloudflared → `127.0.0.1:3000`; `/data` bind mount (db + config.yaml); all host-specific config as env (`AUTH_MODE`, `DEV_AUTH_TOKEN`, `APP_BASE_URL`, …) for open-source portability; dev-token auth bypass (token + email, auto-create); per-user bank settings in DB at account creation; self-setup guide written at implementation.
- [Lock the Google-only auth model](issues/05-google-auth-model.md) — Google `sub` as PK; backend OAuth PKCE (scopes openid/email/profile); refresh token in SQLite; server-side `sessions` table (one per device) with ~30-day sliding cookie, silent renewal; sign-out revokes Google token; empty state at first login; `owner_user_id` FK scoping; sharing (06) = Google email, redirect URI = tunnel domain.
- [Design read-only sharing between users](issues/06-readonly-sharing.md) — share grants one income source (months, settlements, slips) read-only; share by Google email, pending until first sign-in; status ledger never deleted — `pending`/`active`/`dismissed`/`rejected`, receiver sees data only while `active`; one row per (owner, sharee, source); owner-only, no onward sharing; sharee can dismiss, un-dismiss unless rejected; rejected vanishes from sharee's list; "shared by me"/"shared with me" lists show status + last change; shared rows never copied (server-side read filter), mutations reject shared rows; source delete cascade-deletes shares, deactivate keeps them; PDF slips only, no CSV.
- [Model income sources, projects & currency inheritance](issues/02-model-income-sources.md) — Income Source carries name, mutable currency, optional fixed salary, a commission mode (% of value or flat per project); Project inherits its source's currency, commission lands by approval date; Salary Month closes **per source** (settlement per source per month), fully closed only when every active source is closed; glossary published to `CONTEXT.md`. Unblocks 03 and 04.
- [Mechanics of multi-currency forecasting](issues/04-multi-currency-forecast.md) — Forecast = per-view calculation, never stored: 3-month window (selector) from the first not-fully-closed month, extended to include any project's estimated end. Salary every active month; not-yet-settled projects (approved or unpaid) land by estimated end (source's default 6wk), overdue ones carry forward to the current month. One hourly `latest/USD` poll, pairs cross-derived (`source→MXN = (source/USD) ÷ (MXN/USD)`), one snapshot for the whole window, no per-month projection. `gross_MXN = gross_foreign × live_rate`; estimated bank-net `= gross_MXN × (1 − bank%) − fixed_fee` (one transfer/source/month); net-after-tax `− 2%`; rows show gross + net per source with expandable project breakdown; 2 decimals. No rate >48h → that source in own currency with warning, excluded from MXN totals. Ripple: 02's "lands by approval date" is really *by payment selection at close* (carry-over possible); 01's close picks the projects feeding the one-vs-per-project toggle.
- [Validate the settlement math](issues/01-validate-settlement-math.md) — Formula accepted provisionally; prototype at `prototypes/01-settlement-math.html` (one/multiple transfers, one-vs-per-project toggle, decimals OK, round-trip 0.00). **Reopen after first real paycheck to validate against bank numbers** — the lock to re-verify.

## Not yet specified

<!-- in-scope fog you can't ticket yet; graduates as the frontier advances -->

- **The build itself** is next: this map is now a complete spec. Implementation starts with the tracer-bullet tickets; nothing structural remains undecided.
- **01's real-world validation** is still deferred — reopen *Validate the settlement math* after the first real paycheck to plug in bank-statement numbers and lock the formula.

## Out of scope

<!-- work ruled beyond the destination; closed, never graduates -->

- **The build itself** — destination is the spec; implementation is later sessions.
- **Cloudflare Tunnel setup** — the human does this themselves (salary.glappet.eu).
- **The 2% tax rate** — a given, not something to research.