# Executor / Anthares-browser status — 2026-10-12 21:27 -04:00

Scope: shared status for agents working on the legacy rebuild and Anthares-browser. No real publication is authorized by this document.

## Current routing

1. CircleCI — primary. `provider_smoke` invokes `ci/shared/anthares-browser-runtime-qa.sh`, which runs the canonical 40 isolated Docker cases. Current checks are being created for main commits but remain pending in CircleCI while multiple agents are pushing concurrently.
2. Bitrise — secondary. `bitrise.yml` invokes the same canonical 40-case browser QA script.
3. Render — tertiary runtime/browser-control fallback. It is independent hosted compute and its services are active, but it is NOT yet equivalent evidence to the Dockerized 40-case CI proof.

GitHub Actions is manual diagnostic only because hosted-runner allocation was repeatedly queued before jobs received machines. GitLab hosted CI is currently blocked by `ci_quota_exceeded`. Cirrus is retired from active routing and must not be treated as a live redundancy provider.

Canonical routing file: `ci-hub/executor-routing.json` revision `2026-10-12-executors-r4`.

## Anthares-browser runtime facts

- Historical repository path remains `anthares-brouser/`; product name is Anthares-browser.
- Chromium CDP remains bound to `127.0.0.1:9222` inside the container and is not externally published.
- FastAPI control endpoints require bearer auth.
- Browser profile persists at `/data/chrome-profile`.
- `start.sh` sets `NO_PROXY/no_proxy` for loopback so inherited HTTP proxy settings cannot intercept the local CDP WebSocket.
- `/health` is liveness only. `/ready` is the fail-closed browser/profile readiness endpoint.
- Current `/ready` also rejects an unwritable profile directory and intentionally reports `durable_volume_verified=false` unless external infrastructure proves durability.
- Session evidence is fail-closed: profile persistence is not authentication proof.
- Latest production-vault/runtime-mesh work from other agents is present on main; do not overwrite it with the older standalone browser implementation.

## QA correction now on main

Commit `b8f6830763237442a02988d193c0dcd0f2f2394d` corrected the canonical 40-case test after `/health` and `/ready` were separated. The QA now:

- validates `/health` only as liveness;
- waits for and validates `/ready` before CDP operations, including again after profile restart;
- keeps the existing auth, loopback-only CDP, navigation, click, type, wait, evaluate, screenshot, noVNC and profile-restart checks;
- prints the exact failing API method/path/status/body and container logs instead of masking a future HTTP 503 behind `curl -f`.

This prevents the previous false failure mode where a correct liveness response was tested as if it still contained browser-readiness fields.

## Proof boundary

Do not mark the current Anthares-browser 40-case proof as complete until a post-`NO_PROXY` independent-provider run succeeds on a commit containing the corrected readiness QA. The older GitHub runs that returned HTTP 503 checked out pre-fix SHAs and therefore do not prove the current implementation failed.

Kwai authentication and real publication remain separate gates; this status file does not authorize either.