# 05 - Lock the Google-only auth model

Type: grilling
Status: resolved
Blocked by:

## Question

Lock the authentication model.

- Charting confirmed: **Google Sign-In only** — no email/password.
- Decide: identity shape (Google sub as user id, email, display name), the user model, first-login onboarding (empty state, add your first income source), and how the app scopes data per user (ownership of income sources, projects, months).
- What happens on session expiry / token refresh, and whether any server-side session store is needed.

## Notes / context

- Sharing (06) and deployment/redirect URIs (07) both hang off this model.
- Deployment target: self-hosted behind Cloudflare Tunnel — OAuth redirect URI must match the tunnel domain.

## Comments

- Input from *Pick the deployment + Cloudflare Tunnel shape* (07): exactly one OAuth redirect URI on the public hostname `https://conteo.YOUR_DOMAIN/<path>`; the final path is decided here. `AUTH_MODE=dev` + `DEV_AUTH_TOKEN` give a token+email dev-login (auto-creates the user, same session-cookie path) so the app is testable before Google OAuth exists. First-login onboarding must collect per-user bank settings before adding an income source.

## Comments

- **Q1 (identity shape)** — Google `sub` is the primary key; email + display name stored as mutable attributes, re-synced at each login.
- **Q2 (first-login)** — detected by data: a user with zero income sources sees the empty state ("Add your first income source"); no onboarding flag.
- **Q3 (OAuth flow)** — backend authorization-code + PKCE; Google client secret server-side; refresh token held in SQLite; frontend never sees Google tokens.
- **Q4 (session)** — server-side opaque HttpOnly/Secure/SameSite=Lax cookie bound to a `sessions` table; ~30-day sliding expiry.
- **Q5 (expiry/refresh)** — backend silently refreshes via stored Google refresh token; on Google rejection redirect to Google sign-in; 401 → frontend redirects.
- **Q6 (scoping)** — `owner_user_id` FK on every owned row (income sources, projects, months); server-side filtering only; sharing (06) overlays read-only grants.
- **Q7 (sign-out)** — delete the session row + clear the cookie, and revoke the Google refresh token (fresh, consent-free flow next time).
- **Q8 (multi-device)** — many concurrent sessions (one row per device); each has its own cookie and sliding expiry; sign-out from one device leaves the rest alive.
- **Q9 (renewal ceiling)** — silent indefinite renewal while the Google refresh token validates; no hard cap. Tradeoff (stolen cookie stays good) accepted for family-scale app, mitigated by revocable sessions + Google revocation at sign-out.
- **Q10 (scopes)** — `openid email profile` only; no Gmail/contacts/Drive access. Sharing (06) matches typed emails against our DB.
- **Q11 (user row)** — `sub` (PK), `email`, `display_name`, `avatar_url`, `created_at`, `last_login_at`.

## Answer

**Locked Google-only auth model:**

- **Identity** — Google `sub` as PK; `email`, `display_name`, `avatar_url`, `created_at`, `last_login_at` on the `users` row; email/name re-synced at each login.
- **Flow** — backend OAuth authorization-code + PKCE; client secret server-side only; scopes `openid email profile` (no Gmail/contacts).
- **Tokens** — Google refresh token stored in SQLite per user; ID token verified at callback.
- **Sessions** — server-side `sessions` table, one row per device; opaque HttpOnly/Secure/SameSite=Lax cookie; ~30-day sliding expiry; silent indefinite renewal while refresh token validates; 401 → frontend redirects to Google sign-in.
- **Sign-out** — delete session row + clear cookie + revoke Google refresh token.
- **First login** — zero income sources → empty state ("Add your first income source"); no onboarding flag.
- **Scoping** — `owner_user_id` FK on every owned row (income sources, projects, months); server-side filtering only.
- **Contracts for 06/07** — sharee identity = Google email; OAuth redirect URI = tunnel domain, read from config not hardcoded.