# 08 - Research live FX data sources

Type: research
Status: resolved
Blocked by:

## Question

Which free, live FX data source should the app use for USD→MXN and SEK→MXN (and any currency an income source uses)?

Constraints from the brief:

- Live feed with updates roughly every 20 minutes.
- Free tier (personal use), no/minimal API key friction, no hard rate-limit pain for a single user polling a handful of currency pairs.
- Reliable uptime and reasonably current rates for MXN pairs.
- Fits a Python FastAPI backend (simple HTTP/JSON).

## Notes / context

- This is AFK: resolve with a `/research` subagent.
- Only the *provider choice* is researched here; forecast mechanics (04) and settlement (01) decide how rates get used.
- Findings land on a throwaway `research/` branch with a context pointer from this ticket.

## Answer

**Recommended: open.er-api.com** (`https://open.er-api.com/v6/latest/USD`) — no API key, plain JSON, verified live to include both MXN (17.06) and SEK (9.56). Rates refresh once per 24h, so the app polls hourly (no free source hits the ~20-min cadence; Open Exchange Rates' free tier is closest at hourly but needs a key and caps at 1,000 req/month). Battle-tested since 2010 with an EOL warning field for deprecation.

**Fallback chain**: open.er-api.com → Frankfurter v2 (`api.frankfurter.dev`, zero quotas, verified) → last cached snapshot as final safety net.

Full comparison + failure behavior in `research/08-fx-source.md`.