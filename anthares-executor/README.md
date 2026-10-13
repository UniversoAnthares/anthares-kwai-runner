# Anthares-Executor (independent remote Chromium runtime)

A containerized, provider-neutral alternative to Cloudflare Browser Run and Render. Source branch: `feature/anthares-reserva-ci`.

**Implementation status:** code committed, not deployed, no live Kwai session or publication verified. This is an executor foundation, not a completed social publishing adapter.

## Runtime contract

- HTTP `GET /health` reports Chromium readiness and memory without secrets.
- Protected `POST /v1/browser/start` and `POST /v1/browser/stop` manage a single isolated Chromium process.
- Protected `POST /v1/jobs`, `GET /v1/jobs/{id}`, `POST /v1/jobs/{id}/complete` implement idempotent local fenced jobs.
- `lease` is a high-entropy opaque value; `generation` is the controller's monotonic fencing generation.
- API requires `ANTHARES_EXECUTOR_TOKEN`; compose binds only to `127.0.0.1:8080`, not the public internet.
- Profile and SQLite volumes survive container restarts on the same host. **Cross-host recovery is not yet implemented.**
- A browser can be started and inspected by the *local* CDP interface; no remote CDP port is exposed.

## Deployment prerequisites

Requires a remotely hosted Linux machine with Docker, >= 2 GiB RAM recommended, persistent disk and an authorized secure tunnel/reverse proxy. No machine or free provider has yet been validated for these requirements. Do not deploy on the user's PC. Never open port 8080 directly to the internet or place tokens in the repository.

From a remote machine, after securely configuring `ANTHARES_EXECUTOR_TOKEN`, run `docker compose up -d --build` in this directory. Verify the health endpoint, test that protected routes return 401 without a token, then test Chromium start and stop with an authorized request.

## Production gates

1. Confirm free remote host capacity and deployment.
2. Verify memory, restart and persistent profile.
3. Integrate an authorized controller with single-writer lease/fencing and heartbeats.
4. Implement encrypted cross-host session migration and verify authenticated Kwai account.
5. Verify upload interface and one authorized real publication, with deduplication and audit evidence.
6. Only after these pass consider promoting the executor; keep existing Render and Cloudflare paths as fallbacks.

**Current scope does not perform any real social publication.**
