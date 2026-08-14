# ADR-0001: pnpm is the only allowed package manager

Status: accepted

## Context

The frontend is a Next.js app. Both `package-lock.json` (npm) and
`pnpm-lock.yaml` had been committed, and the npm-style `overrides` field was
used to pin patched `postcss`/`sharp` versions. pnpm v11 ignores overrides in
`package.json` (it no longer reads any settings from the `pnpm` field), so
the audit fixes silently did not apply under pnpm — only npm honoured them.

The maintainer prefers pnpm. Keeping two lockfiles and two override formats
is a maintenance and security footgun.

## Decision

- **pnpm is the only package manager** allowed in this repo. `npm install`
  (and the npm lockfile) are not used; do not add `package-lock.json` back.
- Package manager and version are pinned via the `packageManager` field in
  `frontend/package.json` (`pnpm@11.21.0`).
- Dependency-resolution settings live in `frontend/pnpm-workspace.yaml`:
  `allowBuilds` (esbuild, sharp, unrs-resolver) and `overrides`
  (`postcss@^8.5.26`, `sharp@^0.35.3`) to keep the audit clean.
- Docker builds use Corepack to activate the pinned pnpm, then
  `pnpm install --frozen-lockfile` (see `Dockerfile`).

## Consequences

- One lockfile (`frontend/pnpm-lock.yaml`) is the source of truth.
- The `overrides`/`allowBuilds` settings are honoured by pnpm v11.
- Any instruction in this repo that needs a package-manager command must
  spell out `pnpm`, never `npm`.