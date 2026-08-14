# Salary Tracker & Forecaster

A multi-user personal-finance app for a contractor in Mexico City: tracks income sources (fixed salary + linked projects, each source in its own currency), forecasts future salary months with live FX to MXN, settles months against the exact amount that hits the bank, and produces PDF salary slips.

## Income & Projects

**Income Source**:
A counterparty that pays income in one currency (e.g. "US company" in USD). Carries an optional fixed salary, a commission mode, an incoming currency, and linked projects.
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