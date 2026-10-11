# Instagram official API

- UTC: 2026-10-11T21:27:10Z
- Status: PARTIAL
- Area: official Instagram content publishing

## Evidence

Implemented `scripts/instagram_publish.py` using the official container flow: live quota query, Reel container creation, container status polling, and `media_publish`. The default host is `graph.instagram.com` for Instagram Login; `INSTAGRAM_GRAPH_HOST` can select the Facebook Login host.

Added `.github/workflows/instagram-official-publish.yml` with `workflow_dispatch` and `repository_dispatch` entry points. The workflow supports `quota` and `publish-reel`, reads credentials only from GitHub secrets, and runs unit tests before execution.

Added `test-hub/test_instagram_publish.py` covering runtime quota parsing, container creation parameters, processing status, exhausted-quota protection, publish flow, and token transport through the Authorization header.

## Security

The access token is never emitted by the publisher and is sent through the Authorization header. Tests use synthetic credentials only.

## Required runtime configuration

- Secret `INSTAGRAM_USER_ID`
- Secret `INSTAGRAM_ACCESS_TOKEN`
- Optional variable `INSTAGRAM_API_VERSION` (default `v26.0`)
- Optional variable `INSTAGRAM_GRAPH_HOST` (default `graph.instagram.com`)

## Next validation

Run the pull-request unit-test workflow. After the two Instagram secrets exist on the repository, dispatch `quota` to verify the account's live `quota_total`, then perform one controlled `publish-reel` with a public MP4 URL.
