# 04 - Mechanics of multi-currency forecasting

Type: grilling
Status: resolved
Blocked by: 02

## Question

How does the forecast work once income sources can be in different currencies?

- Forecast horizon: 3 months default, configurable.
- Each source converts its fixed salary + expected commissions to MXN via a live FX feed for its currency.
- Projects are real assigned ones; estimated end = start + 6 weeks (overridable), landing commission in the estimated month.
- Which live rates are needed (USD→MXN, SEK→MXN, …), and how the forecast handles a currency with no recent rate.

Specify the forecast calculation: per-month aggregation, which sources/projects land in which month, and how live rates feed in.

## Notes / context

- Blocked on the income-source model (02).
- FX data source itself is researched under 08; this ticket decides the forecast mechanics, not the provider.

## Comments

### Round 1 (grilling) — settled

- **Horizon**: next N months from the first not-fully-closed month; a project whose estimated end falls beyond the window **extends** the horizon (the setting is a minimum, not a hard cap). Flagged: the 6-week estimated-end default may belong on the income source (see R2 Q8).
- **Forecast vs actual**: a month is a *forecast* until fully closed — nothing is actual until the money lands and the user closes. Closed months show their recorded actuals.
- **Approved projects stay expected**: even an approved project may not be paid until a later month, so it stays *expected* until the money is registered at close. This reshapes the settlement flow — the close must let the user **select which not-yet-settled projects are paid this month** (carried-over approvals possible) and choose per-project transaction structure. → recorded for 01/02 as a model update.
- **Rates**: open months use live data (single `latest/USD`, cross-derived); closed months use the bank's derived rate stored immutably per month (no inheritance). Always show the source's currency and its conversion to the user's bank currency.
- **Same live rate across the whole open horizon** — no per-month rate projection.
- **No recent rate**: ~48h staleness threshold; degrade gracefully — render that source in its own currency with a warning, exclude from MXN totals, don't block the view.
- **Gross + estimated net**: forecast shows gross MXN conversion *and* an estimated-net column applying current fee/%/tax settings (values' scoping from 03).

### Round 2 (grilling) — settled

- **Current month is forecast too**: nothing is actual until the month is closed — we always call it a forecast until then (bank rate unknown until money lands + manual close). No "actual" labels in the forecast view, even for partly-settled months.
- **Model amendment → 02/01 (recorded)**: approval ≠ payment. A project can be approved and paid in a *later* month. The close flow must let the user **select which not-yet-settled projects are paid this month** (per-project include checkbox) plus the one-vs-per-project transfer toggle (01). Commission lands in settlement by *payment selection at close*, not strictly by approval date. Needs to be folded into 02's answer + CONTEXT.
- **Closed months**: keep their own bank-derived rate and all their data in their own row; no inheritance from elsewhere. Open months use the live rate.
- **Cadence**: user open to 1–4 fetches/day; 08 already fixed polling hourly. Settled: keep hourly poll of `latest/USD` (cross-derived), display uses latest snapshot.

### Round 3 (grilling) — settled

- **Overdue unpaid projects** carry forward into the current (first) forecast month until paid.
- **Horizon configurability**: per-view selector, default 3, not a saved setting.
- **Estimated-net formula** (forecast has no typed bank-net, so it estimates): `gross_foreign × live_rate × (1 − bank%) − transfers × fixed_fee` → bank-net, then `− 2% tax` → net-after-tax; **one transfer per source per month** (per-project transfer choice exists only at close). Fee/%/tax values + scoping deferred to 03.
- **Display**: one row per income source (source currency + MXN conversion) with expandable per-project breakdown.
- **Forecast is a calculation, not a stored table** — recomputed from live rates each view over the months not yet fully closed.

### Round 4 (grilling) — settled

- **Rounding**: 2 decimals everywhere.
- **Extended months** (from a project pushing the window out): show the full expected month — salary + landing commission — not commission-only.
- **Currency change mid-horizon**: the current currency applies to all window months (no mid-horizon switch modeling).

## Answer

**Window** — per-view selector, default 3 months, from the first not-fully-closed month (current month included). A project whose estimated end falls past the window extends the horizon to include it (selector is a minimum). Extended months show the full expected month for active sources. Forecast covers open months only; closed months keep their own bank-derived rate and data.

**Landing** — fixed salary every month the source is active (current value, flat full-month); every not-yet-settled project (approved or not) lands by its estimated end (start + source's default 6 weeks, overridable); approved-but-unpaid projects stay expected until paid; overdue projects carry forward into the current month until settled. Currency changes use the current currency for all window months.

**FX** — one hourly poll of `latest/USD`; all pairs cross-derived (`source→MXN = (source/USD) ÷ (MXN/USD)`); one snapshot shared across the whole forecast, no per-month projection. Rows show source currency + MXN conversion. No recent rate (>48h stale or missing): that source renders in its own currency with a warning, excluded from MXN totals; rest still renders.

**Math** — per source per month: `gross_MXN = gross_foreign × live_rate`; estimated bank-net `= gross_MXN × (1 − bank%) − fixed_fee` (one transfer per source per month); net-after-tax `= bank-net × (1 − 2%)`. Rows show gross MXN and estimated bank-net; one row per source, expandable per-project breakdown; monthly totals; 2 decimals. Fee/%/tax values and scoping from 03. Forecast is computed on view, never stored.

**Ripple to other tickets** — 02: approval ≠ payment; close flow selects which unsettled projects were paid this month (carry-over). 01: the close's per-project selection feeds the one-vs-per-project transfer toggle.

Status: resolved