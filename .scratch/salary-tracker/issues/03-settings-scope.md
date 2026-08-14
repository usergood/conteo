# 03 - Decide global vs per-income-source settings

Type: grilling
Status: resolved
Blocked by: 02

## Question

Where do the settings live — global to the user, or per income source?

- Bank fixed fee (320 MXN default), bank conversion %, commission %, tax % (2%).
- The user's current reality is a single Mexican bank account for everything; a future Swedish customer still pays into the same CitiBancoMex account. So the bank settings look global, but commission % may differ per income source (the US 8% vs a future Swedish agreement).

Decide the scoping for each setting, and which are per-user vs per-source.

## Notes / context

- Only resolvable once the income-source model (02) defines what a source holds.
- Charting flagged commission % as a setting early on; the income-source reframe in Q2 raises the per-source question.

## Comments

- Input from *Pick the deployment + Cloudflare Tunnel shape* (07): business settings live as **per-user rows in the DB** (bank info: currency, fixed fee, commission %), collected at account creation before any income source is added. Scoping (global vs per-source) is still this ticket's call.

## Answer

Settings scope, agreed by grilling:

- **Bank fixed fee (320 MXN default)** — **global per-user**. One bank per user is an enforced limit for now; every source pays into that one account, so one fee.
- **Bank conversion %** — **global per-user**. Assumption: the bank charges the same fee for all incoming currencies.
- **Tax % (2%)** — **global per-user**, stored in the user's bank/tax settings. Applies to all bank-net MXN regardless of source origin.
- **Commission %** — **per income source**, default **0**. A source can have % of project value, a flat amount per approved project, or no commission income at all (both 0). Seed value is 0, not the 8% default; the user's real 8% is set on their actual source.
- **Bank currency (MXN)** — **global per-user** (per 07).

**Change semantics**: forward-only, matching 02's rate-locking — closed settlements keep their recorded amounts; edits to any setting affect open settlements, future months, and the forecast only.

**Bank/tax settings row (per-user, collected at account creation per 07)**: currency, fixed fee, conversion %, tax %. Commission % is **not** part of this row — it is a per-source field. This ripples back to 07's config.yaml seed list: drop the 8% commission seed (commission defaults to 0 per source).