# Salary Tracker & Forecaster

A self-hosted multi-user personal-finance app for contractors in Mexico: tracks income sources (fixed salary + linked projects, each in its own currency), forecasts future months with live FX to MXN, settles each month against the exact amount that lands in the bank, and produces PDF salary slips.

- **Stack**: Python FastAPI backend, Next.js/React frontend, SQLite storage, Docker.
- **Auth**: Google Sign-In only (dev-login bypass available for testing).
- **Deploy**: single container behind a Cloudflare Tunnel.

This guide walks a fresh instance from zero to running. It assumes a Linux host with Docker, and a domain you can point DNS at.

## Architecture

One container runs everything: Next.js (standalone) serves the web app and rewrites `/api/*` to FastAPI on an internal, unexposed port. Nothing outside the container is persisted except one data directory.

```
Internet → Cloudflare Tunnel → 127.0.0.1:3000 (container web port)
                                    └─ /api/* → FastAPI (internal)
```

The container mounts one host directory at `/data`:

- `salary.db` — SQLite database
- `config.yaml` — non-secret defaults (currency MXN, 2% tax, 320 MXN bank fee) that seed the account-creation form

## Pre-provisioning (one-time)

These steps are done by you, on your own accounts; nothing in the app can do them for you.

### 1. Create the Cloudflare Tunnel

Create a named tunnel for `salary.glappet.eu` and get its credentials token. cloudflared runs on the host (see below) and points at the app's web port.

### 2. DNS

Add a proxied CNAME on your zone:

```
salary.glappet.eu  CNAME  <tunnel-uuid>.cfargotunnel.com  (proxied)
```

### 3. Google OAuth client

Create an OAuth client at <https://console.cloud.google.com/apis/credentials>:

- Authorized JavaScript origin: `https://salary.glappet.eu`
- Redirect URI: `https://salary.glappet.eu/api/auth/callback`

Take note of the Client ID and Client Secret.

### 4. Host directory

Create the data directory on the host and pre-seed `config.yaml`:

```bash
mkdir -p ~/salary-tracker
cat > ~/salary-tracker/config.yaml <<'EOF'
currency: MXN
tax_percent: 2
bank_fixed_fee: 320
EOF
```

`config.yaml` holds only non-secret defaults used to pre-fill the account-creation form. All secrets and host-specific values go in environment variables, never in the file.

## Run

```bash
docker run -d \
  --name salary-tracker \
  --restart unless-stopped \
  -p 127.0.0.1:3000:3000 \
  -v ~/salary-tracker:/data \
  -e AUTH_MODE=google \
  -e GOOGLE_CLIENT_ID=<client-id> \
  -e GOOGLE_CLIENT_SECRET=<client-secret> \
  -e SESSION_SECRET=<random> \
  -e APP_BASE_URL=https://salary.glappet.eu \
  -e WEB_PORT=3000 \
  salary-tracker:latest
```

### Environment variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `AUTH_MODE` | yes | — | `google` or `dev` |
| `DEV_AUTH_TOKEN` | no | — | Enables the dev-login bypass; absent → Google-only |
| `GOOGLE_CLIENT_ID` | yes (google) | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | yes (google) | — | Google OAuth client secret |
| `SESSION_SECRET` | yes | — | Secret for signing session cookies |
| `APP_BASE_URL` | yes | — | Public address, e.g. `https://salary.glappet.eu`; drives redirect URIs / absolute links |
| `WEB_PORT` | no | `3000` | Host-facing web port (bound to 127.0.0.1) |

Only the web port is published, bound to `127.0.0.1`; FastAPI is never directly reachable. TLS terminates at Cloudflare; the origin is plain HTTP.

### cloudflared

Run a tunnel pointing at the app:

```bash
cloudflared tunnel --url http://127.0.0.1:3000
```

Or, with a named tunnel and the credentials file from step 1:

```bash
cloudflared tunnel --name salary run
```

## Dev / test mode

Before the tunnel and Google OAuth client exist, the app is fully usable with the dev-login bypass:

```bash
docker run -d \
  --name salary-tracker-dev \
  -p 127.0.0.1:3000:3000 \
  -v ~/salary-tracker:/data \
  -e AUTH_MODE=dev \
  -e DEV_AUTH_TOKEN=<your-token> \
  -e SESSION_SECRET=<random> \
  -e APP_BASE_URL=http://127.0.0.1:3000 \
  salary-tracker:latest
```

The dev-login screen takes the token plus an email, auto-creates the user if missing, and issues the same session cookie the Google flow would.

## Open-source portability

Everything host-specific is an environment variable (see table above); nothing is hardcoded. `config.yaml` holds only non-secret seed defaults. This keeps the project safe to open-source — running it elsewhere is just a different set of env vars.

## Backups

Everything that matters lives in `/data` (`salary.db` + `config.yaml`). Back up that directory (e.g. `sqlite3 salary.db .backup` or a plain file copy); the container itself is disposable.