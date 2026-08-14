# 01 - Validate the settlement math against real bank numbers

Type: prototype
Status: resolved
Blocked by:

## Question

Is the month-close settlement formula correct? Proposed flow:

- User enters the exact MXN that hit the CitiBancoMex account (the bank-net, after the bank's % and its fixed fee).
- Settings hold the bank's static % and the fixed fee (320 MXN default).
- App derives the effective rate the bank used:
  `rate = (typed_MXN + fixed_fee) ÷ (USD_paid × (1 − bank%))`
- Tax = 2% of the typed bank-net; the slip shows bank-net and bank-net − tax side by side.

Build a cheap calculator prototype (numbers in, numbers out) and run real-world examples from the user's bank statement against it. Confirm the derivation handles: single vs multiple USD transfers in a month, and the "one transfer vs per-project transfers" option at close.

## Notes / context

- User confirmed the direction in Q1/Q2 of the charting grilling but explicitly wants real-world example validation before this is locked.
- Bank fee: 320 MXN per transfer (setting). Bank %: static on conversion (setting). Tax: 2% of bank-net (setting).
- "Projects included in the month are always approved before the close button is pushed" — so USD paid for the month is fully known at close.

## Assets

- Calculator prototype: `prototypes/01-settlement-math.html` (open by double-click).

## Answer

Formula accepted, on provisional terms. The derivation `rate = (typed_MXN + transfers × fixed_fee) ÷ (USD_paid × (1 − bank%))` and the bank-net vs bank-net−tax slip are correct and handle single transfer, multiple transfers (blended rate), and the one-vs-per-project close toggle (verified against scenario numbers; round-trip = 0.00 by construction). Bank % accepts decimals (e.g. 1.5, 3).

**Not yet validated against real bank numbers** — deferred until the first real paycheck. Reopen this ticket then, plug the bank statement figures into the prototype, and lock the formula. No blockers: the rest of the spec can proceed.

## Comments

- 2026-08-13 — Claimed. Built a logic prototype (`prototypes/01-settlement-math.html`): a pure `settlement` module (reducer + `derive`) renders one transfer / multiple transfers / the one-vs-per-project close toggle / typing-sensitivity, with the round-trip check and the bank-net vs bank-net−tax slip side by side. Verified against scenario numbers: single and multi-transfer blend to the same rate; the close toggle moves the derived rate by ~0.15 MXN/USD; round-trip is 0.00 by construction.
- 2026-08-13 — User: formula "feels right for now"; keep this open and revisit **after the first real payment in a month** — changes may be needed then. Confirmed the bank % field already accepts decimals (parseFloat + step="any"), e.g. 1.5 or 3; hint text updated to say so. Real-world validation deferred to after first payment.