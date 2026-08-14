# 11 - UI foundations: responsive layout, theming, i18n, dev-login gating

Type: grilling
Status: resolved
Blocked by: 05, 07

## Question

Lay the UI groundwork before implementation starts. The whole-interface prototype (02) exposed four cross-cutting requirements that every screen must inherit:

1. **Responsive layout** — the web app needs both desktop and mobile support. One responsive shell, not two apps.
2. **Dev-login gating** — the dev-login form must be reachable only under the dev env flag; production shows the Google button only.
3. **Light + dark mode** — both themes, system-following default, manual override.
4. **i18n** — English and Spanish only for now, structured so more languages slot in later.

## Notes / context

- Prototype feedback (2026-08-13): views didn't navigate reliably when driven through the walkthrough (fixed in the rewrite); desktop + mobile, theme, and i18n were called out as requirements before implementation.
- 07 already decided: `AUTH_MODE=google|dev`, `DEV_AUTH_TOKEN` present → dev-login bypass. This ticket fixes the production behavior explicitly.
- 05: user row exists (`sub`, email, display_name, avatar_url, created_at, last_login_at) — language joins this row.

## Comments

- **Q1 (default language)** — **English default**, per-user in DB (on the `users` row). User switches in Settings; the choice follows them across devices. Translation keys structured as a flat dictionary per locale so adding a third language is a new file, not a refactor.
- **Q2 (theme)** — **Follow system (`prefers-color-scheme`) by default; per-device override** persisted in `localStorage`. No theme preference sent to the server; each device keeps its own choice.
- **Q3 (dev-login gating)** — **Gated by `AUTH_MODE` env**. `AUTH_MODE=google` → Google Sign-In button only (backend OAuth PKCE). `AUTH_MODE=dev` + `DEV_AUTH_TOKEN` set → token+email dev form. Dev affordances are unreachable in production; nothing dev is ever rendered by `AUTH_MODE=google`.

## Answer

UI foundations, agreed by grilling:

- **Responsive shell** — one responsive layout: desktop (≥~1024px) uses a persistent sidebar nav; mobile collapses to a bottom tab bar. Same routes, same components, CSS-media-query driven. Mobile-first, touch targets ≥44px.
- **Dev-login gating** — `AUTH_MODE=google` renders only the Google button; `AUTH_MODE=dev` renders the token+email form. Hard-coded by the env flag at the server-rendered/app-boot boundary; not a client-side toggle.
- **Theming** — CSS custom properties (`--bg`, `--ink`, `--line`, `--accent`, …) powering `[data-theme="light"|"dark"]`; default follows `prefers-color-scheme`; a header toggle sets `data-theme` and persists the override in `localStorage` (per-device). All existing prototype tokens already map 1:1.
- **i18n** — flat key→string dictionaries, one per locale: `en.ts` / `es.ts` (groundwork: `zh.ts` etc. later). A `t(key)`/`useI18n` hook resolves via the user's language from the DB (fallback `en`). The `users` row gains a `language` column. Number/currency formatting via `Intl` with the locale; MXN amounts still render as `$` + `MXN` per 09. Both themes and both languages demonstrated in the 02 prototype rewrite.

Ripples: `users.language` column (05's user row); Settings screen gains Language and theme toggle; prototype 02 rewritten to show desktop + mobile frames, gated login, theme toggle, and an EN/ES switcher.