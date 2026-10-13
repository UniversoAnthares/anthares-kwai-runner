# Anthares-Executor

Provider-neutral remote Chromium runtime intended to replace Cloudflare Browser Run as the primary browser execution layer while keeping Cloudflare and Render available as fallbacks during migration.

## Implemented

- Containerized Chromium with CDP bound to loopback only.
- Fail-closed Bearer authentication on every state-changing/read-sensitive endpoint.
- Single-writer SQLite jobs with monotonic fencing generations, expiring leases, heartbeats, idempotent completion and stale-lease rejection.
- Encrypted cross-host Chromium profile snapshots in GitLab using AES-GCM; generation manifests are committed last and restore falls back to the previous valid generation.
- Protected profile restore/snapshot endpoints; Chromium must be stopped while profile state is moved.
- Read-only Kwai identity and Studio surface probe for the expected account. It never clicks upload/publish controls and never returns cookies, storage values, page text or tokens.
- Multi-provider controller with health-based priority, cooldown and heartbeat loss fail-closed behavior.
- GitHub-hosted on-demand executor (`Anthares Cloud Executor`) that builds and runs the same Docker image remotely. Its default push mode is a real Chromium runtime self-test. The authenticated probe is an explicit workflow-dispatch mode and only runs when encrypted profile secrets are configured.
- CI contract validation builds the Docker image and starts/stops a real Chromium instance inside it.

No endpoint in this component publishes social content.

## Runtime API

Public:

- `GET /health`

Protected by `Authorization: Bearer <ANTHARES_EXECUTOR_TOKEN>`:

- `POST /v1/browser/start`
- `POST /v1/browser/stop`
- `POST /v1/profile/restore`
- `POST /v1/profile/snapshot`
- `POST /v1/kwai/probe`
- `POST /v1/jobs`
- `POST /v1/jobs/{id}/heartbeat`
- `POST /v1/jobs/{id}/complete`
- `GET /v1/jobs/{id}`

## Environment

Required for a persistent service:

- `ANTHARES_EXECUTOR_TOKEN`: high-entropy API token, minimum 20 characters.

Optional execution settings:

- `ANTHARES_EXECUTOR_ID` (default `reserva-01`)
- `CHROME_PROFILE_DIR` (default `/data/profile`)
- `STATE_DB` (default `/data/state/jobs.sqlite3`)
- `MEMORY_LIMIT_BYTES` (default 1 GiB)
- `LEASE_TTL_SECONDS` (default 180, bounded 30..1800)
- `KWAI_EXPECTED_ACCOUNT` (default `lucasrosalem`)

Encrypted cross-host profile recovery requires:

- `GITLAB_TOKEN`
- `GITLAB_STATE_KEY` (minimum 32 characters; the cloud workflow can map the legacy `CONTROL_TOKEN` secret to this variable for compatibility with the previously-created snapshot)
- `GITLAB_STATE_PROJECT` (default project `87307279`)
- `GITLAB_STATE_BRANCH` (default `browser-state`)
- `GITLAB_STATE_SLOT` (default `runtime`)

Secrets must be configured in the hosting provider/repository secret store. Never put their values in the repository, URLs or job payloads.

## GitHub-hosted zero-cost execution path

Workflow: `.github/workflows/anthares-cloud-executor.yml`.

`runtime-selftest` is safe and credential-free: it builds the production container, starts Chromium remotely, verifies CDP health and shuts it down.

`authenticated-kwai-probe` restores the encrypted profile, starts Chromium, verifies the expected Kwai profile plus the Studio upload surface, stops Chromium and writes a fresh encrypted snapshot only after a successful probe. The workflow stores only a sanitized one-day result artifact. It does not publish.

This path is on-demand rather than an always-running HTTP service, so it avoids Cloudflare Browser Run's browser-minute/rate-limit model and does not depend on the user's PC.

## Persistent-host deployment

`compose.yaml` remains available for any remote Linux/Docker provider. The external reverse proxy/tunnel must expose only the HTTP API; never expose port 9222/CDP. The local compose binding defaults to loopback.

A persistent host is useful for low-latency jobs, but it is no longer a prerequisite for remote Chromium execution because the GitHub-hosted path provides an ephemeral executor.

## Acceptance state

Validated in CI:

- Python API/controller contracts.
- Authentication failure behavior.
- Job idempotence, heartbeats, expiry/reacquisition and fencing.
- Docker image build.
- Real Chromium start, readiness and stop inside the container.

Still requires live evidence before promotion to the primary authenticated Kwai path:

- Successful restore of the existing encrypted profile in the new executor environment.
- `identity_verified=true` for `@lucasrosalem`.
- `upload_surface_verified=true` for Kwai Studio.

Real publication is deliberately outside the acceptance probe and requires a separate explicit authorization.
