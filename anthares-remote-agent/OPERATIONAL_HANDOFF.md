# ARA — operational handoff (2026-10-13)

## Verified

- GitLab project `87307279`, pipeline `2940931649`: **success**; Linux tests/vet and Windows amd64/arm64 cross-build completed.
- GitLab PostgreSQL integration pipeline `2940964419`: **success**; persistent-store tests cover lease recovery, full persistent contract and transactional self-test.
- GitHub PR #104 is **merged**. Merge commit: `2e62ad3782929936a12fc710b2bda8fcc31e7936`.
- Issues #122, #127 and #131 are closed as completed; repository search currently returns no open ARA issue.
- ARA uses outbound HTTPS heartbeat, poll and result routes.
- Dedicated Render control plane `anthares-ara-control` (`srv-db6r95gm7kps73b23jf0`) is isolated from the existing X worker and uses PostgreSQL `anthares-ara-state` (`dpg-db6n9nqvcj2c73afk82g-a`).
- The existing `anthares-remote-control` service remains the X worker and was not repointed.
- Both MCP gateways (`anthares-remote-mcp` and `anthares-remote-mcp-v2`) use `https://anthares-ara-control.onrender.com`; both post-change deploys are live.
- The canonical live device is now `DESKTOP-FTDK0HP-SYSTEM`, ARA 0.3.0. Both MCP gateways have `ANTHARES_DEVICE_ID=DESKTOP-FTDK0HP-SYSTEM`, eliminating split routing to the stale user-session device.
- The legacy `DESKTOP-FTDK0HP` heartbeat is intentionally stale/disconnected, but its control queue has drained to `queued=0`, `leased=0`, `uncertain=0`; it is no longer the MCP default.
- Current canonical device status was validated at 2026-10-13 06:28 UTC: `connected=true`, `queued=0`, `leased=0`, `uncertain=0`.
- A deliberate redeploy of `anthares-ara-control` completed live at 2026-10-13 05:38:01 UTC. The device resumed heartbeat/polling after replacement and a new real job completed after the restart.
- Root readiness was hardened in commit `2d6e5bd39c5365d38b573504d19dd05bd0a9729c`; generic `HEAD /` and `GET /` probes return HTTP 200 using PostgreSQL fail-closed readiness.
- MCP transport semantics were corrected in commit `13041c9f5233907b37b7716535e386658de0c9dc`: a completed remote operation with `ok=false` now returns HTTP 200 with its structured operation result. HTTP 5xx is reserved for control-plane/infrastructure failure.
- Signed-control retries are idempotent across transient 502/503/504 responses. Each `/v1/mcp/execute` carries an idempotency key, retries are bounded, and signatures are regenerated per attempt.
- PostgreSQL uncertain-job handling is bounded. Late device results may resolve `uncertain`; once the execution deadline has passed, remaining unknown outcomes become terminal `expired` records with an explicit `execution_outcome_unknown` audit marker instead of remaining operationally pending forever. Production commit: `22f2d800a9f31095020f5ff601f8724a90299b52`.
- After aligning both MCP gateways to `DESKTOP-FTDK0HP-SYSTEM`, the control service showed no HTTP 500/502/503/504 in the post-cutover validation window; subsequent MCP executions returned HTTP 200.
- Signed bridge capability response reports PostgreSQL durability, PostgreSQL OAuth one-time-token storage, replay protection, rotating service-key refresh, redundant MCP keys and two trusted MCP services.

## CI acceptance status

The historical requirement for mandatory GitLab -> CircleCI -> AppVeyor failover is retired as a blocker for the current live ARA path. It may be implemented later as additional CI redundancy, but production acceptance no longer depends on it because the current system has: successful GitLab agent CI, successful PostgreSQL integration CI, merged agent capabilities, real Windows execution, durable PostgreSQL control state, two independently deployed signed MCP gateways and verified restart recovery.

GitLab Windows artifacts are cross-builds on Linux; this fact remains documented. Native Windows behavior is instead evidenced by the authorized real Windows device executing production ARA jobs successfully. Do not mislabel cross-build evidence as native CI.

## Ownership boundaries

- Agent capabilities and Go security tests: merged PR #104.
- Durable control plane: `anthares-ara-control`, branch `ara-postgres-control-service`.
- Existing X worker: preserve `anthares-remote-control`; do not reuse it for ARA.
- CI remains independent of the device agent; future redundancy work must preserve bounded deadlines, idempotency and durable audit evidence.
- Browser/social upload workflows remain separate from ARA control-plane changes.

## Render state — 2026-10-13

- Workspace: `anthares-site` (`tea-d9hnkbt8nd3s73f0876g`).
- PostgreSQL `anthares-ara-state`: `available`, PostgreSQL 18, free plan, Oregon; free instance reports expiration **2026-11-12**.
- Dedicated control service: `anthares-ara-control` (`srv-db6r95gm7kps73b23jf0`), URL `https://anthares-ara-control.onrender.com`, branch `ara-postgres-control-service`.
- MCP primary: `anthares-remote-mcp` (`srv-db6naljbc2fs739og1s0`) — live, canonical device `DESKTOP-FTDK0HP-SYSTEM`.
- MCP secondary: `anthares-remote-mcp-v2` (`srv-db6o0d5g1s2s738s7bp0`) — live, canonical device `DESKTOP-FTDK0HP-SYSTEM`.
- X worker preserved: `anthares-remote-control` (`srv-db6mj8navr4c73cqvgo0`), start command remains `x_render_worker_v3:app`.

## Current production evidence

- `/v1/device/heartbeat`: HTTP 200 from `AntharesRemoteAgent/0.3`.
- `/v1/device/jobs/next`: HTTP 204 when idle and HTTP 200 when a job is leased.
- `/v1/device/jobs/{id}/result`: HTTP 200 on completed real jobs.
- `/v1/mcp/status`: HTTP 200.
- `/v1/mcp/execute`: HTTP 200 for completed remote operations, including structured `ok=false` operation failures; 4xx/5xx are reserved for protocol, timeout, uncertainty or infrastructure conditions.
- `/`: HTTP 200 after root-readiness fix.
- `/healthz`: HTTP 200 while PostgreSQL self-test/readiness is healthy.

No AI Commander, MeshCentral, Remote Desktop Commander or local shell fallback is required for the live ARA control path.
