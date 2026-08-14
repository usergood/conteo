# 07 - Pick the deployment + Cloudflare Tunnel shape

Type: grilling
Status: resolved
Blocked by:

## Question

Specify the deployment target.

- Charting confirmed: self-hosted (own server) behind a **Cloudflare Tunnel** on the deployer's own domain.
- Decide: the docker packaging (FastAPI + Next.js + SQLite), where config + db are mounted outside the container, env/config approach for the settings (bank fee, bank %, commission %, tax %), and the OAuth redirect URI story against the tunnel domain.
- What the user must pre-provision (tunnel, domain DNS, Google OAuth client) before the app can be stood up.

## Notes / context

- The human will set the tunnel up themselves later; this ticket writes down the contract the app expects.
- Auth model (05) feeds the redirect-URI detail — but the packaging shape is decidable here.

## Answer

Deployment shape, agreed by grilling:

**Packaging** — one container: Next.js (standalone) + FastAPI + SQLite. Next.js serves the app and rewrites `/api/*` to FastAPI on an internal, unexposed port. Nothing outside the container is persisted except the data dir.

**Build tooling** — the frontend is built with **pnpm only** (never npm): version pinned via the `packageManager` field in `package.json`, settings (`allowBuilds`, `overrides`) in `pnpm-workspace.yaml`, and the Dockerfile uses Corepack + `pnpm install --frozen-lockfile`. See ADR-0001. No `package-lock.json` is committed.

**Tunnel / routing** — single public hostname `https://conteo.YOUR_DOMAIN` → one origin. cloudflared runs on the host, pointing at `http://127.0.0.1:3000`. Only the web port is published, bound to localhost; FastAPI is never directly reachable. TLS terminates at Cloudflare; the origin is plain HTTP.

**Mount** — one host directory (e.g. `~/conteo/`) bind-mounted at `/data` inside the container. Holds:
- `conteo.db` — SQLite data
- `config.yaml` — non-secret defaults (currency MXN, 2% tax, 320 MXN bank fee) used to seed the account-creation / onboarding form. (No commission % seed — commission defaults to 0 per source per 03.)

**Settings storage** — business settings are **per-user rows in the DB**: bank info (currency, fixed fee), collected at account creation, before any income source is added. (Commission % is **not** in this row — see *Decide global vs per-income-source settings* 03: commission % is a per-source field, default 0.) This is a scoping input to *Income-source settings scope* (03) and a first-login-onboarding input to *Google-only auth model* (05).

**Config / secrets — all env, none hardcoded** (portability for open-sourcing). The container consumes:
- `AUTH_MODE` = `google` | `dev`
- `DEV_AUTH_TOKEN` — enables the dev-login bypass; absent → Google-only
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET`
- `APP_BASE_URL` — the public host address (e.g. `https://conteo.YOUR_DOMAIN`); drives redirect URIs / absolute links
- `WEB_PORT` — host-facing web port (default 3000, bound to 127.0.0.1)

**Dev/test auth** — `AUTH_MODE=dev` + token: a dev-login screen takes the token + an email, auto-creates the user if missing, and issues the same session cookie the Google flow would. The app is fully buildable and testable before the tunnel and Google OAuth client exist.

**OAuth redirect** — exactly one redirect URI on the public hostname, `https://conteo.YOUR_DOMAIN/<path>` (final path lands under *Google-only auth model* 05), same-origin, no localhost in production.

**Human pre-provisioning** (later, out of scope for now) — cloudflared tunnel created; `CNAME conteo.YOUR_DOMAIN → <tunnel-uuid>.cfargotunnel.com` (proxied); Google OAuth client with authorized JS origin `https://conteo.YOUR_DOMAIN` and the redirect URI; host dir created. All written up as a self-setup guide (README) in implementation, since the project will be open-sourced.

## Comments

- Q1/Q2: single container; single hostname, one origin, internal `/api` proxy.
- Q3: single mapped drive `/data` for db + config.
- Q4: settings per-user in DB, set at account creation (ripples to 03, 05).
- Q5: secrets/env via compose `environment:`.
- Q6: publish only web port to `127.0.0.1`, cloudflared → `http://127.0.0.1:3000`.
- Q7: one OAuth redirect URI on the public hostname; raised dev-token idea.
- Q8: dev token as env + `AUTH_MODE` gate.
- Q9: token + email, auto-create user, same session-cookie path.
- Q10: pre-provisioning checklist confirmed; host address env-driven for open-source self-setup; instructions written during implementation.