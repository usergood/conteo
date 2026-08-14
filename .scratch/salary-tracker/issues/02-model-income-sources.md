# 02 - Model income sources, projects & currency inheritance

Type: grilling
Status: resolved
Blocked by:

## Question

What exactly is an **Income Source**, and how do projects attach to it?

The charting grilling surfaced this model: an income source is the unit of income (e.g. "US company" in USD, future "Swedish customer" in SEK). It carries a fixed salary, an incoming currency, and optional linked projects. Projects inherit their income source's currency.

Sharpen the model via grilling + domain-modeling:

- Fields of an income source (name, fixed salary amount, currency, commission % per source or global?).
- Fields of a project (value, assigned date, estimated end date defaulting to start + 6 weeks, approval date) and how it links to its income source.
- How a salary month aggregates: fixed salary + approved-project commissions per income source.
- The glossary vocabulary for the whole domain (Source, Project, Commission, Approval, Salary Month, Settlement, etc.).

## Notes / context

- Charting Q2 established: fixed salary + income currency per source; projects optional per source, currency inherited.
- Charting Q5: forecast uses only real assigned projects (estimated end = start + 6 weeks, overridable); no assumed pipeline.
- This is the keystone ticket — 03 and 04 are blocked on it.

## Comments

### Round 1 (grilling) — settled

- **Commission**: 8% of full project value, single lump on approval. No caps, minimums, or staged payments.
- **Currency**: strictly inherited from the income source; no per-project override.
- **Source shapes**: both pure-salary (no projects) and commission-only (no fixed salary) sources are valid; fixed salary optional per source.
- **Partial-month salary**: flat full-month regardless of start date. Settlement may set a lower value manually at month close (corrects reality).
- **Salary month**: calendar month aggregating (a) the source's fixed salary + (b) every approved project whose approval date falls in that month; sums per source, then across sources.
- **Approval vs estimated end**: both dates stored. Forecast lands commission by estimated end (start+6wk, overridable); settlement lands it by real approval date.

### Round 2 (grilling) — settled

- **Commission % field**: lives on the income source. **Can be either a % of project value OR a fixed amount per approved project** — the mode is set on the source.
- **Fixed salary over time**: single current value on the source; each salary month holds its own final value, **inherited from the source until close, then overridable at month close** (sickness/vacation → lower value). No salary-history table; updating the source re-defaults future months, closed months keep their written amount.
- **Source lifecycle**: deactivate keeps closed months, drops source out of forecast; rename freely; delete only when the source is completely empty (no months, no projects).
- **Closed months frozen, never reopened**: the user always closes/approves projects *before* closing the month (they close 1–3 days after the company pays, waiting for money to land in the Mexican account). So a project approved after a close simply belongs to the next month; a closed month's amounts are immutable.
- **Glossary confirmed** as proposed (Income Source, Fixed Salary, Project, Commission, Approval, Salary Month, Settlement, Bank-Net, Forecast).

### Round 3 (grilling) — settled

- **Commission modes**: a source has exactly one mode — either % of project value or a flat amount per approved project — applied to all its projects. No per-project override.
- **Rate locking**: commission/salary rates are captured at month close and written into that month; later changes on the source only affect future months and the forecast. Closed months immutable.

### Round 4 (grilling) — per-source closing

- **Per-source settlement**: each income source is closed **independently** (payments land on different dates). A salary month is **fully closed only when every active income source for that month is closed**. The PDF slip is only available once all sources for the month are closed.
- Each source close records its own bank-net MXN, its own derived FX rate, and the per-source commission/salary breakdown. This crystallizes the map's "transfer structure" fog item: closing is per source, not per month.

### Round 5 (grilling) — settled

- **Every active source must be closed each month**, even with zero projects (project income = 0, but the fixed salary still comes — common in a source's first month). A source stays in the month's close list while active; skipping it only happens when it's not active.
- **One Settlement per source per month**; the "one transfer vs per-project transfers" fee math is ticket 01's job. The model records one bank-net per source close.
- **No backfill, no activation date**: a source's months begin the month it's added; prior months are never created for it.

### Round 6 (grilling) — settled

- **Currency is mutable**: a source's incoming currency can change, but never retroactively — closed settlements keep their recorded amounts; only future payments and the simulated future (forecast) are affected.
- **No concurrency cap**: any number of projects per source; the "up to 3 concurrent" from the brief is the user's personal reality, not a model constraint.

## Answer

**Income Source** — name (renamable), incoming currency (mutable forward-only), optional fixed salary (single current value, overridable per month at close), commission mode (**% of value OR flat amount per approved project**, one mode per source), linked projects. No activation date (months start the month the source is added; no backfill), no concurrency cap. Lifecycle: deactivate (drops from forecast, history kept) / rename / delete only when completely empty.

**Project** — value, assigned date, estimated end (start + 6 weeks, overridable), approval date; currency strictly inherited from its source; linked to exactly one source. Commission lands in the month of its approval date (settlement); forecast uses estimated end. *Amendment from 04:* approval ≠ payment — a project approved in month M can be paid in a later month; the close flow lets the user select which not-yet-settled projects are paid this month (carry-over possible), so the settlement month is set by **payment selection at close**, not strictly approval date.

**Salary Month** — one per calendar month; holds per-source fixed-salary values (inherited, overridable at close) and per-source project commissions selected as paid at close; **fully closed when every active source for that month is closed**; immutable once closed.

**Settlement** — one per active source per month, closed independently when its payment lands; records its own bank-net MXN and derived FX rate; per-project vs single-transfer fee math deferred to 01. PDF slip only when all sources for the month are closed.

**Glossary** — published to `CONTEXT.md` (Income Source, Fixed Salary, Project, Commission, Approval, Salary Month, Settlement, Bank-Net, Forecast).