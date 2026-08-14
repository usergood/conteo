# Releasing Conteo

Releases are cut by a human, on the machine, then pushed. Pushing a version tag
is the single trigger: a GitHub Actions workflow builds the Docker image,
publishes it to GHCR, and creates a GitHub Release. **Nothing runs on push to
main** — the tag is the release.

## The version source

The root `VERSION` file is the single source of version truth. It holds a bare
`MAJOR.MINOR.PATCH` (e.g. `0.1.0`). The tag and the file must agree: the release
workflow fails if `git tag vX.Y.Z` does not match the contents of `VERSION`.

## Cut a release

1. **Bump `VERSION`** to the next version, e.g. `0.2.0`.
2. **Commit it** (and any changes for this release) and push to `main`.
3. **Tag and push** the tag:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

   The tag name must be `v` + the exact `VERSION` contents.

That's it. Everything below happens automatically.

## What CI does on a `v*` tag

The [release workflow](.github/workflows/release.yml) runs on `push: tags: ['v*']`:

1. Verifies the tag matches `VERSION`.
2. Builds the Docker image from the existing `Dockerfile`.
3. **Smoke-tests it** — boots the container and hits `/api/health`. A broken
   image fails the workflow here, before anything is published.
4. Pushes both image tags to GHCR:
   - `ghcr.io/usergood/conteo:vX.Y.Z` (pinned to the version)
   - `ghcr.io/usergood/conteo:latest`
5. Creates a GitHub Release with auto-generated changelog notes from the
   commits since the previous tag.

## Regenerate the currency list

The canonical currency list (`backend/app/currencies.json`) is frozen per
release — it is never derived at runtime. If the FX provider's supported set
changed, regenerate it before cutting the release and commit the result:

```bash
python backend/scripts/refresh_currencies.py
```

The script fetches the provider's current codes, keeps the existing names for
codes already in the list, and warns about any new codes that need an ISO 4217
name filled in manually. Edit the file to add those names, then commit.

## Update a deployed instance

The container itself is disposable — everything that matters lives in `/data`.
To deploy a new release, pull the new image and restart the container on the
tunnel host (the exact restart ritual is the private `LOCAL_SETUP.md`):

```bash
docker pull ghcr.io/usergood/conteo:v0.2.0
docker stop conteo && docker rm conteo
docker run -d ... ghcr.io/usergood/conteo:v0.2.0
```

Use the pinned `vX.Y.Z` tag (never `latest`) for production restarts so you
know exactly which version is running.
