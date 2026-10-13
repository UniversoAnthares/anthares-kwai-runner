# Executor / Anthares-browser status — 2026-10-12 21:15 -04:00

Scope: shared status for agents working on the legacy rebuild and Anthares-browser. No real publication is authorized by this document.

## Current routing

1. CircleCI — primary. `provider_smoke` invokes `ci/shared/anthares-browser-runtime-qa.sh`, which runs the canonical 40 isolated Docker cases. Current CircleCI check is active/pending on main.
2. Bitrise — secondary. `bitrise.yml` invokes the same canonical 40-case browser QA script.
3. Render — tertiary runtime/browser-control fallback. It is independent hosted compute and is active, but is NOT yet equivalent evidence to the Dockerized 40-case CI proof.

GitHub Actions is manual diagnostic only because hosted-runner allocation was repeatedly queued before jobs received machines. GitLab hosted CI is currently blocked by `ci_quota_exceeded`. Cirrus is retired from active routing and must not be treated as a live redundancy provider.

Canonical routing file: `ci-hub/executor-routing.json` revision `2026-10-12-executors-r4`.

## Anthares-browser runtime facts

- Historical repository path remains `anthares-brouser/`; product name is Anthares-browser.
- Chromium CDP remains bound to `127.0.0.1:9222` inside the container and is not externally published.
- FastAPI control endpoints require bearer auth.
- Browser profile persists at `/data/chrome-profile`.
- `start.sh` now sets `NO_PROXY/no_proxy` for loopback so inherited HTTP proxy settings cannot intercept the local CDP WebSocket.
- Session evidence is fail-closed: persistence is not authentication proof.
- Latest production-vault work from another agent is present on main; do not overwrite it with the older standalone browser implementation.

## Proof boundary

Do not mark the current Anthares-browser 40-case proof as complete until a post-`NO_PROXY` independent-provider run succeeds. The older GitHub runs that returned HTTP 503 checked out a pre-fix SHA and therefore do not prove the fix failed.

Kwai authentication and real publication remain separate gates; this status file does not authorize either.
