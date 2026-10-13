# ARA — operational handoff (2026-10-13)

## Verified

- GitLab project `87307279`, pipeline `2940931649`: **success** after correcting the CI to test GitHub branch `feature/ara-capabilities`; Linux tests/vet and Windows amd64/arm64 cross-build completed.
- GitLab PostgreSQL integration pipeline `2940964419`: **success**; persistent store tests cover lease recovery, full persistent contract and transactional self-test.
- GitHub PR #104 remains open at `feature/ara-capabilities`; its base is `feature/anthares-remote-agent`.
- ARA uses outbound HTTPS heartbeat, poll and result routes.
- Dedicated Render control plane `anthares-ara-control` (`srv-db6r95gm7kps73b23jf0`) is isolated from the existing X worker and uses PostgreSQL `anthares-ara-state` (`dpg-db6n9nqvcj2c73afk82g-a`).
- The existing `anthares-remote-control` service remains the X worker and was not repointed.
- Both MCP gateways (`anthares-remote-mcp` and `anthares-remote-mcp-v2`) are configured to use `https://anthares-ara-control.onrender.com` and their post-change deploys are live.
- Real Windows device `DESKTOP-FTDK0HP` is connected through ARA 0.3.0. Live `session_status` returned `connected=true`, and a real `system_info` job completed successfully through the durable control plane.
- A deliberate redeploy of `anthares-ara-control` completed live at 2026-10-13 05:38:01 UTC. The device resumed heartbeat/polling immediately after replacement, and a new `system_info` job completed after the restart.
- Root readiness was hardened in commit `2d6e5bd39c5365d38b573504d19dd05bd0a9729c`; generic `HEAD /` and `GET /` probes now return HTTP 200 using the same fail-closed PostgreSQL readiness contract as `/healthz`.
- Signed bridge capability response reports PostgreSQL durability, PostgreSQL OAuth one-time-token storage, replay protection, rotating service-key refresh, redundant MCP keys and two trusted MCP services.

## Remaining external acceptance items

- CircleCI connected project and completed `ara_validation` run: **not verified**.
- AppVeyor connected project and native Windows CI run: **not verified**.
- GitLab -> CircleCI -> AppVeyor CI-provider failover: **not demonstrated**. These are CI redundancy acceptance items; they no longer block the live ARA control path.
- GitLab Windows builds are cross-builds on Linux; they do not replace native Windows CI evidence. The real Windows device execution above proves the production execution path, not AppVeyor acceptance.

## Ownership boundaries

- Agent capabilities and Go security tests: PR #104 / `feature/ara-capabilities`.
- Durable control plane: `anthares-ara-control`, branch `ara-postgres-control-service`.
- Existing X worker: preserve `anthares-remote-control`; do not reuse it for ARA.
- CI orchestration: keep independent of the device agent, with bounded deadlines, idempotency and durable audit evidence.
- Browser/social upload workflows remain separate from ARA control-plane changes.

## Render state — 2026-10-13

- Workspace: `anthares-site` (`tea-d9hnkbt8nd3s73f0876g`).
- PostgreSQL `anthares-ara-state`: `available`, PostgreSQL 18, free plan, Oregon; free instance reports expiration **2026-11-12**.
- Dedicated control service: `anthares-ara-control` (`srv-db6r95gm7kps73b23jf0`), URL `https://anthares-ara-control.onrender.com`, branch `ara-postgres-control-service`.
- MCP primary: `anthares-remote-mcp` (`srv-db6naljbc2fs739og1s0`) — live after control URL correction.
- MCP secondary: `anthares-remote-mcp-v2` (`srv-db6o0d5g1s2s738s7bp0`) — live after control URL correction.
- X worker preserved: `anthares-remote-control` (`srv-db6mj8navr4c73cqvgo0`), start command remains `x_render_worker_v3:app`.

## Current production evidence

- `/v1/device/heartbeat`: HTTP 200 from `AntharesRemoteAgent/0.3`.
- `/v1/device/jobs/next`: active polling with HTTP 204 when idle and HTTP 200 when jobs are leased.
- `/v1/device/jobs/{id}/result`: HTTP 200 on completed real jobs.
- `/v1/mcp/status`: HTTP 200.
- `/v1/mcp/execute`: real executions return HTTP 200 for successful jobs; individual command failures may legitimately surface as HTTP 500 when the agent reports a failed operation.
- `/`: HTTP 200 after root-readiness fix.
- `/healthz`: HTTP 200 while PostgreSQL self-test/readiness is healthy.

No AI Commander, MeshCentral, Remote Desktop Commander or local shell fallback is required for the live ARA control path.
