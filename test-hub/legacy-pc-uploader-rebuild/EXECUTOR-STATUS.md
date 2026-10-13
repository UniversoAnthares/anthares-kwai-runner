# Executor / Anthares-browser status — 2026-10-12 21:46 -04:00

Scope: shared status for agents working on the legacy rebuild and Anthares-browser. No real publication is authorized by this document.

## Current routing

1. CircleCI — primary 40-case Docker proof. A dedicated branch now isolates this proof from the Android backlog: `qa/anthares-browser-isolated`, current proof commit `a69a038a37d56c2d231e37eb52ea1d1f502d5edd`. Its only Circle job is `anthares_browser_qa`. It is pending at the time of this update.
2. Bitrise — secondary. `bitrise.yml` invokes the same canonical 40-case browser QA script; independent branch trigger visibility is not yet proven through GitHub statuses.
3. Render — tertiary independent runtime/control proof. `anthares-browser-qa-render-v2` is LIVE on commit `783538b3afff863062c3edc75888bad47d8bd308` and has already passed live control-plane checks listed below.

GitHub Actions is manual diagnostic only because hosted-runner allocation was repeatedly queued before jobs received machines. GitLab hosted CI is currently blocked by `ci_quota_exceeded`. Cirrus is retired from active routing and must not be treated as a live redundancy provider.

Canonical routing file: `ci-hub/executor-routing.json` revision `2026-10-12-executors-r4`.

## Anthares-browser runtime facts

- Historical repository path remains `anthares-brouser/`; product name is Anthares-browser.
- Chromium CDP remains bound to `127.0.0.1:9222` inside the container and is not externally published.
- FastAPI control endpoints require bearer auth.
- Browser profile is `/data/chrome-profile`.
- `start.sh` sets `NO_PROXY/no_proxy` for loopback and `app.py` also passes explicit `http_no_proxy` to websocket-client, so inherited HTTP proxy settings cannot intercept local CDP.
- `/health` is liveness only. `/ready` is fail-closed browser/profile readiness and performs a real CDP WebSocket `Runtime.evaluate` probe.
- `/ready` rejects an unwritable profile directory and intentionally reports `durable_volume_verified=false` unless external infrastructure proves durability.
- noVNC is loopback-only inside the container; the corrected canonical QA tests it from inside the container rather than exposing port 6080.
- Session evidence is fail-closed: profile persistence is not authentication proof.

## Dedicated 40-case lane correction

The first isolated Circle branch inherited an older QA copy that still expected host-exposed noVNC. That result would have been invalid after the security change. The branch was therefore synchronized with current main without changing its minimal single-job Circle config. Commit `a69a038a37d56c2d231e37eb52ea1d1f502d5edd` now uses current blobs for:

- `ci/shared/anthares-browser-runtime-qa.sh` (`8d8e611f3105031384e27ff8d551b7d1af248d40`);
- `anthares-brouser/app.py` (`cadb510ea1d4e8fd6f6ae211e6c95293d293f0e1`);
- `anthares-brouser/start.sh` (`05425164231b18b54fbbc85bdee2702e8c5dcd82`).

The isolated Circle job remains pending. Do not spawn additional Circle jobs while this one is waiting.

## Render independent proof

A first Render deployment exposed a hosted-runtime mismatch: main `start.sh` hardcodes API port 8080, while Render requires `$PORT`; Render reported no open public port. Rather than alter main semantics, a dedicated branch `qa/anthares-browser-render` was created. Commit `783538b3afff863062c3edc75888bad47d8bd308` binds uvicorn to `${PORT:-8080}` and keeps the API process alive for diagnostics while `/ready` remains fail-closed if Chromium/CDP is unavailable.

Render service `anthares-browser-qa-render-v2` (`srv-db6ootl9fdbs73do9sm0`) reached LIVE. Direct live tests passed:

- `/health`: HTTP 200, correct Anthares-browser liveness contract;
- `/ready`: HTTP 200 with profile present+writable, Chromium running, CDP ready, `durable_volume_verified=false`;
- authenticated `/status`: HTTP 200, non-empty Chromium PIDs, CDP bind `127.0.0.1:9222`, session claim `not_verified`;
- unauthenticated `/status`: HTTP 401;
- `/page`: HTTP 200 and real page state from Chromium;
- `/evaluate`: HTTP 200 and correct document title;
- `/screenshot`: HTTP 200, PNG payload with valid PNG base64 prefix;
- `/navigate`: HTTP 200 to a real HTTPS form;
- `/wait`: selector found;
- `/type`: text inserted and independently read back through `/evaluate`;
- `/click`: DOM control clicked and independently verified as checked.

This proves the current control API + Chromium + loopback CDP + auth + navigate/wait/type/click/evaluate/screenshot path on an independent hosted runtime. It does NOT prove durable storage across instance replacement, real Kwai authentication, publication, or the full 40-case restart matrix.

## Cross-agent finding

The active `feature/ara-infra` implementation of `wait_for_job()` already treats `uncertain` as a terminal state alongside done/failed/expired. Canary commit `6f4fb9037e9b79b606899fd5b91e275b61274eb1` adds a regression test proving it returns immediately without sleeping. This is useful confirmation for the Anthares Remote agent, but it remains canary-branch evidence until that agent promotes/tests the intended production branch.

## Proof boundary

Anthares-browser runtime/control path is now independently proven on Render. The complete 40-case Docker/profile-restart proof remains pending on the isolated CircleCI job. Do not conflate either result with Kwai authentication or publication. No social publication occurred in this work.

## Recheck — 2026-10-12 22:16 -04:00

- CircleCI isolated proof `a69a038a37d56c2d231e37eb52ea1d1f502d5edd`: GitHub combined status now reports `failure` for `ci/circleci: anthares_browser_qa` (workflow `515cbf1c-5291-4ced-805a-be88021bf3cc`, job `ee3f41d2-8242-4f47-bfd3-64f506209d45`). The previous `pending` statement above is superseded. CircleCI job logs are not accessible through the current GitHub connector or public page, so root cause is **not established**; do not claim 40-case pass or apply speculative fixes. Obtain failing step/log before modifying QA or spawning another run.
- Render `anthares-browser-qa-render-v2` service and deployment independently rechecked: service active/not suspended, latest deploy `dep-db6oou59fdbs73do9u70` status `live`, commit `783538b3afff863062c3edc75888bad47d8bd308`, auto-deploy disabled. This is the earlier runtime proof, not proof of newer main changes.
- Main has since received authenticated noVNC gateway commit `7a38477e24d0b83453431f6f5e1245182842d475` (23 tests reported by commit message) and router fail-closed commit `3d3b9886f481fc1c20090266d7b5dbcc8934b94a` (15 tests reported by commit message). Neither commit is contained in the isolated Circle proof SHA or the Render deploy SHA; these claims need independent CI/runtime verification.
- A separate coordination-evidence lease is active until `2026-10-13T02:30:00Z`; do not overwrite that agent's coordination target. No publication/scheduler change.


## CircleCI restriction / replacement audit (2026-10-12 local)

- User-provided screenshot of `circleci.com/error/login-abusive/` confirms CircleCI account access restriction (Acceptable Use Policy). Treat CircleCI as `BLOCKED_ACCOUNT`, not as a trustworthy signal of browser QA code regression. Do not route new CI jobs to it or request user to retry login.
- Isolated replacement lane created on branch `qa/anthares-browser-github-fallback`, commit `45b152361f37b1dce1937f28c9de32e1b2a7533c`. It changes ONLY `.github/workflows/anthares-brouser-runtime-qa40.yml` on that branch to execute the existing canonical 40-case Docker QA on push/manual dispatch; no production workflow/main changes. A GitHub Actions run was **not yet observed** through connector (commit-run wrapper only surfaces PR runs). Treat as CONFIGURED, not PASS.
- Parallel-to-Render system located: `tools/RENDER_REDUNDANCY.md` and `tools/provider_router.py` on main. Cloudflare `anthares-control` holds durable queue/leases/fencing, while Render/GitHub Actions/GitLab SaaS are execution providers. `tools/render_redundancy_acceptance.py` covers simulated failover, not a live Docker executor. The control plane by itself **cannot** execute the Anthares-browser Docker 40-case matrix. GitLab SaaS runner previously blocked by quota; GitHub Actions is the viable independent fallback to test, pending an actual runner/job proof. Anthares Remote Control currently deployed **on Render** (`anthares-remote-control.onrender.com`), so it is not independent Render hosting.
- Browserless reached free-plan usage cap during read-only Cloudflare endpoint probe; web tool could not reach the Workers endpoint. No live Cloudflare status claim made in this audit. No scheduler or social publication changes.
