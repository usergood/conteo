<p align="center">
  <img src="frontend/public/conteo.svg" width="120" alt="Conteo logo">
</p>
<h1 align="center">Conteo</h1>
<p align="center"><em>Spanish for "counting"</em> — a self-hosted income tracker that counts, forecasts, and settles every income source in your own currency.</p>
<h1 align="center">&nbsp;</h1>

A self-hosted multi-user income tracker for an IT consultant with customers or employers in different countries: track each income source (fixed salary + linked projects, each in its own currency), forecast expected income with live FX, record the final income that lands in the bank each month, and produce PDF salary slips — all the data you need when doing taxes.

The app logo lives in one canonical place — `frontend/public/conteo.svg` — and is reused as the favicon, the in-app header/login mark, and on the exported PDF salary slips (`frontend/public/conteo.png` is a raster derived from it for PDF embedding).

- **Stack**: Python FastAPI backend, Next.js/React frontend, SQLite storage, Docker.
- **Auth**: Google Sign-In (optional — a dev-login bypass covers local/DEV runs without any Google setup).
- **Deploy**: single container behind a Cloudflare Tunnel. Images are published to GHCR and pulled by tag — see the [Run](#run) section and [RELEASING.md](RELEASING.md) for the release ritual.

This guide walks a fresh instance from zero to running. It assumes a Linux host with Docker, and a domain you can point DNS at.

> **Pick your host up front.** Every deployment must set its own public address via `APP_BASE_URL`; nothing is hard-coded to a specific domain. If you don't have (or don't want) a public host and Google auth, skip straight to [Dev / test mode](#dev--test-mode) — the app runs fully locally with `AUTH_MODE=dev`, no domain or OAuth client required.

> Owners: your personal, filled-in copy of this guide (real host, tunnel and OAuth credentials) lives in the git-ignored `LOCAL_SETUP.md`.

## Architecture

One container runs everything: Next.js (standalone) serves the web app and rewrites `/api/*` to FastAPI on an internal, unexposed port. Nothing outside the container is persisted except one data directory.

```
Internet → Cloudflare Tunnel → 127.0.0.1:3000 (container web port)
                                    └─ /api/* → FastAPI (internal)
```

The container mounts one host directory at `/data`:

- `conteo.db` — SQLite database
- `config.yaml` — non-secret defaults (currency MXN, 2% tax, 320 MXN bank fee) that seed the account-creation form

## Pre-provisioning (one-time)

These steps are done by you, on your own accounts; nothing in the app can do them for you.

### 1. Create the Cloudflare Tunnel

Create a named tunnel for your public hostname (e.g. `conteo.YOUR_DOMAIN`) and get its credentials token. cloudflared runs on the host (see below) and points at the app's web port.

### 2. DNS

Add a proxied CNAME on your zone:

```
conteo.YOUR_DOMAIN  CNAME  <tunnel-uuid>.cfargotunnel.com  (proxied)
```

### 3. Google OAuth client

Create an OAuth client at <https://console.cloud.google.com/apis/credentials>:

- Authorized JavaScript origin: `https://conteo.YOUR_DOMAIN`
- Redirect URI: `https://conteo.YOUR_DOMAIN/api/auth/callback`

Take note of the Client ID and Client Secret.

### 4. Host directory

Create the data directory on the host and pre-seed `config.yaml`:

```bash
mkdir -p ~/conteo
cat > ~/conteo/config.yaml <<'EOF'
currency: MXN
tax_percent: 2
bank_fixed_fee: 320
EOF
```

`config.yaml` holds only non-secret defaults used to pre-fill the account-creation form. All secrets and host-specific values go in environment variables, never in the file.

## Run

Published images are pulled from **GHCR** (a local `docker build` is not needed).
Always pin a `vX.Y.Z` tag for production so you know exactly which version is
running; see [RELEASING.md](RELEASING.md) for the release ritual and how to
update a deployed instance.

```bash
docker run -d \
  --name conteo \
  --restart unless-stopped \
  -p 127.0.0.1:3000:3000 \
  -v ~/conteo:/data \
  -e AUTH_MODE=google \
  -e GOOGLE_CLIENT_ID=<client-id> \
  -e GOOGLE_CLIENT_SECRET=<client-secret> \
  -e SESSION_SECRET=<random> \
  -e APP_BASE_URL=https://conteo.YOUR_DOMAIN \
  -e WEB_PORT=3000 \
  ghcr.io/usergood/conteo:v0.1.0
```

### Environment variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `AUTH_MODE` | yes | — | `google` or `dev` |
| `DEV_AUTH_TOKEN` | no | — | Enables the dev-login bypass; absent → Google-only |
| `GOOGLE_CLIENT_ID` | yes (google) | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | yes (google) | — | Google OAuth client secret |
| `SESSION_SECRET` | yes | — | Secret for signing session cookies |
| `APP_BASE_URL` | yes | — | Public address of *your* instance, e.g. `https://conteo.YOUR_DOMAIN`; drives redirect URIs / absolute links. Must match your own host — nothing is hard-coded |
| `WEB_PORT` | no | `3000` | Host-facing web port (bound to 127.0.0.1) |

Only the web port is published, bound to `127.0.0.1`; FastAPI is never directly reachable. TLS terminates at Cloudflare; the origin is plain HTTP.

### cloudflared

Run a tunnel pointing at the app:

```bash
cloudflared tunnel --url http://127.0.0.1:3000
```

Or, with a named tunnel and the credentials file from step 1:

```bash
cloudflared tunnel --name conteo run
```

## Dev / test mode (no host, no Google auth)

Before a public host and Google OAuth client exist — or for any local run — the app is fully usable with the dev-login bypass. No domain, tunnel, or OAuth client is required; just set `AUTH_MODE=dev` and your own `DEV_AUTH_TOKEN`:

```bash
docker run -d \
  --name conteo-dev \
  -p 127.0.0.1:3000:3000 \
  -v ~/conteo:/data \
  -e AUTH_MODE=dev \
  -e DEV_AUTH_TOKEN=<your-token> \
  -e SESSION_SECRET=<random> \
  -e APP_BASE_URL=http://127.0.0.1:3000 \
  ghcr.io/usergood/conteo:latest
```

The dev-login screen takes the token plus an email, auto-creates the user if missing, and issues the same session cookie the Google flow would.

## Development

Frontend tooling is **pnpm only** (ADR-0001) — never run `npm` in this repo:

```bash
cd frontend
pnpm install
pnpm run dev
```

`pnpm install` uses the committed `pnpm-lock.yaml`; the pinned version is set in `package.json` via `packageManager` and Docker builds activate it with Corepack.

## Open-source portability

Everything host-specific is an environment variable (see table above); nothing is hard-coded. `config.yaml` holds only non-secret seed defaults. Each deployer supplies their own `APP_BASE_URL` (their host) or runs `AUTH_MODE=dev` locally without any host or Google setup. This keeps the project safe to open-source — running it elsewhere is just a different set of env vars.

## Backups

Everything that matters lives in `/data` (`conteo.db` + `config.yaml`). Back up that directory (e.g. `sqlite3 conteo.db .backup` or a plain file copy); the container itself is disposable.
