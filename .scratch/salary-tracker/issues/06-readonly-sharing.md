# 06 - Design read-only sharing between users

Type: grilling
Status: resolved
Blocked by: 05, 02

## Question

How does read-only sharing work?

- Charting confirmed: sharing is **read-only**; a user can have their own income sources, and shared ones arrive read-only (for the wife's SAT work).
- Decide the sharing primitive: is a share granted per income source (and its months/slips), or per month? Who can share, with whom (by Google email), can a share be revoked, and what exactly a sharee sees (months, slips/PDFs, live data or only closed?).
- How ownership + shares compose: one user's source shared read-only into another's view, without mutating the owner's data.

## Notes / context

- Blocked on the auth model (05) and the income-source model (02).
- Primary use case: the wife sees the user's closed-month salary slips for her SAT filing.

## Comments

### Round 1 (grilling) — settled

- **Granularity**: a share grants one **income source** (all its months, settlements, commissions, and PDF slips composed from it). A sharee sees a month's aggregate slip only when they can see **every source contributing to that month**. Revocation is per source.
- **Governance**: only the **owner** can share; shares are never onward-shareable; revocation is immediate (sharee loses access on next request); re-sharing the same source to the same email is idempotent.
- **Invitee**: share by **Google email** (05 contract). If the email has no account yet the share sits **pending** and activates on that email's first sign-in.
- **Sharee view**: full-fidelity read-only — name, currency, fixed salary, projects, commissions, settlements, derived FX/fees/tax, and downloadable PDF slips; **both open and closed months** shown, all read-only.
- **Composition**: shared data lives in a cleanly separated area ("Shared with me"), read-only, badged, **never aggregated** into the sharee's own totals/forecast/settlements. If multiple people share with one user, a picker shows **one sharer at a time**; the user's own views stay primary.
- **Source lifecycle**: deactivate keeps shares working (sharee keeps closed months, source drops from live view); rename propagates live (read-through, no copy); delete (only when empty) cascade-deletes its shares.

### Round 2 (grilling) — settled

- **Revoke mechanics**: hard revoke — access cut immediately, no undo. A later phase may add Export/Import to replace sharing for copy-out workflows; for now just revoke. Revoke also works on **pending** shares.
- **Sharee-side control**: the receiver **can dismiss** a shared source (their choice). Both the sharer and the receiver see the **status of all their shares** — owner has a "shared by me" list, receiver a "shared with me" list.
- **Sharee view scope** (confirmed): a read-only mirror of exactly the shared sources — months, settlements, slips, and forecast — never the owner's unshared data. Aggregate month slip is visible only when every source contributing to that month is shared (and closed).
- **Export**: PDF slips only, no CSV.
- **Model (with statuses)**: `shares` table with statuses beyond active/pending — **`rejected`** (sharer denies further access) and **`dismissed`** (receiver no longer wants to see it) — so the "shared by me" and "shared with me" lists can surface state.

### Round 3 (grilling) — settled

- **Status model (clarified)**: share rows are **never deleted** — the `shares` table is a status ledger, not a delete-on-revoke store ("hard revoke" was about *data deletion*, not share records). The receiver sees the shared source's data **only while the status is `active`**; `pending`, `dismissed`, and `rejected` all cut data access. Owner's **"shared by me"** shows every person they've shared with, each row's current status, and when the status last changed. Receiver's **"shared with me"** shows the sharers, the status (active/dismissed/rejected), and when the change happened.
- **Dismissed is reversible**: the receiver can un-dismiss back to `active` on her own — **unless the sharer has `rejected`** the share, which is terminal.
- **Rejected + re-grant**: after rejection, the sharer re-granting is a fresh grant; the rejected share **vanishes from the receiver's list** (supersedes the Round-3 "shared with me shows rejected" wording). The row itself persists on the owner's side.

### Round 4 (grilling) — settled

- **Re-grant mechanics**: one row per (owner, sharee, source); re-grant **re-activates the existing row** (status → pending/active) rather than appending a new one.
- **Activation**: pending shares **silently activate** at the invitee's first sign-in — no notifications on either side; owner's "shared by me" status just flips pending → active.
- **Source-delete reconciliation**: deleting a source (only possible when empty) **cascade-deletes its shares** — the one exception to row persistence.

## Answer

**Locked read-only sharing model:**

- **Granularity** — a share grants one **income source** (all its months, settlements, commissions, and PDF slips composed from it). A sharee sees a month's aggregate slip only when they can see **every source contributing to that month** (and the month is closed). Revocation is per source.
- **Governance** — only the **owner** of a source can share; shares are **never onward-shareable**; the owner can revoke anytime (access cut immediately); re-granting is idempotent.
- **Invitee** — share by **Google email**; if the email has no account yet the share sits **pending** and silently activates on that email's first sign-in.
- **Status ledger** — `shares` rows are **never deleted** except with their source. Statuses: **`pending`**, **`active`**, **`dismissed`**, **`rejected`**. The receiver sees the source's data **only while `active`**; every other status cuts data access (they may still see the status in their list).
- **Transitions** — pending→active (first sign-in, silent); active→dismissed (receiver hides); dismissed→active (receiver un-dismisses on her own, unless the sharer has rejected); any→rejected (owner revokes, terminal); rejected→pending/active (owner re-grants, re-activating the row).
- **Lists** — owner's **"shared by me"** shows every person shared with, each share's status, and when it last changed. Receiver's **"shared with me"** shows sharers, status, and change time — but **rejected shares vanish** from the receiver's list (the row persists for the owner).
- **Composition** — a read-only mirror of exactly the shared sources (months, settlements, slips, and their forecast); **never aggregated** into the sharee's own totals/forecast/settlements; "shared with me" uses a per-sharer picker (one sharer at a time); the user's own views stay primary.
- **Enforcement** — server-side only: read queries filter `owner_user_id = me OR source_id ∈ my active shares`; every mutation endpoint **rejects** shared rows; shared rows are **never copied** — the sharee always reads the owner's live rows (read-through).
- **Source lifecycle** — deactivate keeps shares working (sharee keeps the closed months, source drops from live view alongside the owner's); rename propagates live; delete (only when empty) cascade-deletes its shares.
- **Export** — **PDF slips only**; no CSV. A later phase may add Export/Import for copy-out workflows.
- **Model** — `shares` table: `id`, `owner_user_id` (FK), `sharee_user_id` (nullable FK, set at activation), `pending_email`, `source_id` (FK income_source), `status` (pending/active/dismissed/rejected), `created_at`, `updated_at`; **one row per (owner, sharee, source)**.