# FX Data Source — Free live rates for USD→MXN and SEK→MXN

**Date:** 2026-08-13. Free providers shift frequently; details verified against live endpoints on this date.

## Recommendation

Use **ExchangeRate-API's open-access endpoint** at `https://open.er-api.com/v6/latest/USD` (and `/v6/latest/SEK` for a SEK base). It is a single GET returning plain JSON, needs **no API key and no signup**, and the payload includes both `MXN` and `SEK` (verified live: `USD→MXN 17.060`, `USD→SEK 9.563`). Rates refresh **once per 24h** (the response's `time_next_update_utc` confirms the daily cadence) — so the app should poll on a ~1h schedule at most; polling every 20 minutes gains nothing because the source itself does not move that often (see notes). No free tier anywhere offers the ~20-minute cadence the brief hoped for; hourly is the best any free key-gated plan offers, and the no-key feeds are daily. This endpoint is rate-limited (HTTP 429 after bursts, resets after ~20 min), but a single user polling a handful of pairs once an hour stays far below the abuse threshold. Attribution (a small link back to exchangerate-api.com) is the only obligation. Track record is strong (running since 2010, Pingdom-monitored uptime, and a `time_eol` field that announces deprecation ahead of time), which is why it beats the equally-free ECB-based alternatives on reliability.

Python usage (e.g. with `httpx`):

```python
r = await client.get("https://open.er-api.com/v6/latest/USD")
mxn_per_usd = r.json()["rates"]["MXN"]
```

## Comparison

| Provider | Free? | Key needed? | Refresh | Supports MXN? | Supports SEK? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **open.er-api.com** (ExchangeRate-API open access) | Yes | No | Daily (24h) | Yes (verified) | Yes (verified) | No-key, plain JSON, ~165 currencies, multi-source blended rates. Rate-limited on bursts (429, 20-min reset). Attribution required. Recommended. |
| **Frankfurter v2** — `api.frankfurter.dev` | Yes | No | Daily (ECB/central-bank reference rates, business days ~16:00 CET) | Yes (verified) | Yes (verified) | Open-source (self-hostable), **no quotas at all**, free even for commercial. 84 central banks incl. Banco de México. Old `api.frankfurter.app` now 301s to `.dev`. Best fallback. |
| **exchangerate.host** (APILayer) | Yes | Yes (free key) | Real-time sources, hourly/minutely on paid | Yes | Yes | Free tier only **100 requests/month** — too tight for a polling app. Old no-key endpoint dead; verified it now returns `missing_access_key`. Avoid. |
| **exchangeratesapi.io** (APILayer) | Yes | Yes (free key) | Hourly (free) | Yes | Yes | Free tier **100 requests/month**. Same APILayer umbrella; same quota problem. Avoid for polling. |
| **Open Exchange Rates** (openexchangerates.org) | Yes | Yes (free key) | Hourly (free) | Yes (170+ currencies) | Yes | "Forever Free": 1,000 req/month, **USD base only**, no conversion endpoint, personal use only. Best refresh among free tiers but key-gated with a monthly quota. |
| **exchangerate-api.com** (ER-API keyed tier) | Yes | Yes (free key) | Daily (free) | Yes (161+ currencies) | Yes | Free: 1,500 req/month. This is the keyed sibling of open.er-api.com; no reason to use the keyed one over the open endpoint. |
| **XE Currency Data API** | No | Yes | 10 min on paid | Yes | Yes | **No public free tier** — Lite starts ~$799/yr. Ruled out. |
| **Google Finance** | Unofficial | n/a | Real-time scraped | n/a | n/a | No public API; scraping is against ToS and breaks without notice. Ruled out. |

## Failure / fallback behavior

- **Cache aggressively.** Whatever feed is chosen, fetch on a schedule, store the last-good snapshot, and serve conversions from the cache. A salary tracker tolerates a 24h-old rate perfectly well; never hard-fail the app on a fetch error.
- **Ordered fallback chain:** (1) `open.er-api.com/v6/latest/<base>` → (2) `api.frankfurter.dev/v2/rates?base=<base>&quotes=MXN,SEK` → (3) last cached value, with a `stale` flag surfaced in the response/log so the user knows the rate is old.
- **Handle the 429 explicitly** on open.er-api.com: back off and fall through to Frankfurter rather than retrying hot; the rate limit window is ~20 minutes.
- **Watch `time_eol_unix`** in the open.er-api.com payload — the provider sets it before deprecating an endpoint, so alerting on it gives a migration window instead of a surprise outage.

## Verified URLs (checked 2026-08-13)

- `https://open.er-api.com/v6/latest/USD` — returns MXN + SEK, next update ~24h out
- `https://api.frankfurter.dev/v2/rates?base=USD&quotes=MXN,SEK` — returns MXN 17.0595, SEK 9.5487
- `https://api.frankfurter.app/latest` — 301 → `https://api.frankfurter.dev/v1/...`
- `https://api.exchangerate.host/latest?base=USD&symbols=MXN,SEK` — returns `missing_access_key`
- `https://openexchangerates.org/signup/free` — "Forever Free" plan: 1,000 req/mo, hourly updates, USD base only
- `https://www.exchangerate-api.com/docs/free` — open-access endpoint docs, rate limiting, attribution
- `https://frankfurter.dev/` — v2 docs, provider list, self-hosting, no-quota FAQ
- `https://www.xe.com/sv/business/xecurrencydata` — XE pricing, no free tier
- `https://allratestoday.com/blog/best-free-currency-exchange-api-2026/` — independent 2026 free-tier roundup corroborating the table