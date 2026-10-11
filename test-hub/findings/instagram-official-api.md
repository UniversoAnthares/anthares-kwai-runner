# Instagram official API

- UTC: 2026-10-11T21:30:30Z
- Status: BLOCKED-RUNTIME-CREDENTIALS
- Area: official Instagram content publishing

## Evidence

Implemented `scripts/instagram_publish.py` using the official container flow: live quota query, Reel container creation, container status polling, and `media_publish`. The default host is `graph.instagram.com` for Instagram Login; `INSTAGRAM_GRAPH_HOST` can select the Facebook Login host.

Added `.github/workflows/instagram-official-publish.yml` with `workflow_dispatch` and `repository_dispatch` entry points. The workflow supports `quota` and `publish-reel`, reads credentials only from GitHub secrets, and runs unit tests before execution.

Added `test-hub/test_instagram_publish.py` covering runtime quota parsing, container creation parameters, processing status, exhausted-quota protection, publish flow, and token transport through the Authorization header.

PR #95 was squash-merged into `main` as `0d9898b609ccd9776f080fa8470aa56113b2bcc0`.

GitHub Actions run `38176495445` completed successfully. `py_compile` passed and all Instagram unit tests passed.

Main run `38176566522` completed the unit-test stage successfully. Its credential probe found both `INSTAGRAM_USER_ID` and `INSTAGRAM_ACCESS_TOKEN` absent from GitHub Actions secrets, so the live quota query was skipped. No Instagram content was published during validation.

## Security

The access token is never emitted by the publisher and is sent through the Authorization header. Tests use synthetic credentials only. Live publishing is restricted to explicit `workflow_dispatch` or `repository_dispatch` execution.

## Required runtime configuration

- Secret `INSTAGRAM_USER_ID`
- Secret `INSTAGRAM_ACCESS_TOKEN`
- Optional variable `INSTAGRAM_API_VERSION` (default `v26.0`)
- Optional variable `INSTAGRAM_GRAPH_HOST` (default `graph.instagram.com`)

## Next validation

Configure the two Instagram secrets, dispatch `quota` to read the account's live `quota_total`, then perform one controlled `publish-reel` with a public MP4 URL.
