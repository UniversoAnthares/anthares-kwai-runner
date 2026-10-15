# ARA Phase 4 — redundancy and homologation

Verified at: 2026-10-15T23:22Z

Status: PROVEN

## Production control plane

- Canonical MCP/control backend: Vercel + Neon.
- Canonical production alias: `https://anthares-remote-primary.vercel.app`.
- Production was deliberately redeployed from `dpl_B1Jm7svHUcaxCiLAK8wN9rsgWEvu` to `dpl_3JComNXUH3FKbqCWP7FA2tewY1CX`.
- New deployment reached READY and acquired the canonical production alias.
- The already-authorized ChatGPT Anthares Remote connection remained valid after redeploy; no reconnect was required.
- Post-redeploy `session_status`: connected=true, backend=vercel-neon, queued=0, leased=0, uncertain=0.
- Post-redeploy real Windows execution returned `PHASE4_POST_VERCEL_REDEPLOY_OK` from the canonical `anthares-remote-agent-v4-c8.exe` process.

## Private issue queue redundancy

Recovery transports remain independent inside the same canonical SYSTEM agent:

1. GitLab private issue queue, project `87307279`.
2. GitHub private issue queue, repository `UniversoAnthares/anthares-ara-queue`.

GitHub live proof: issue `#254`, job `ara-phase4-cross-provider-20261015-2320`, executed successfully and returned `PHASE4_GITHUB_EXEC`.

Cross-provider dedupe proof: the same job ID was then delivered through GitLab issue `#95` with a command that would append a second line if re-executed. GitLab returned the already-persisted GitHub result instead. `D:\AntharsWork\temp\ara-phase4-cross-provider.txt` remained at exactly one line (`EXECUTED_ONCE`). Therefore provider failover/failback does not duplicate a previously committed job.

GitLab return-path proof: issue `#96`, job `ara-phase4-gitlab-failback-20261015-2322`, executed independently and returned `PHASE4_GITLAB_FAILBACK_OK`.

## Persistence and recovery conclusions

- Job receipts used by private issue queues are persisted on the Windows executor and survive provider switching/restarts.
- MCP/device state and OAuth/replay state are persisted in Neon, not process memory; Vercel production replacement did not invalidate the live authorization or device state.
- Cloudflare Durable Objects are not in the operational path.
- Render, WinRemote and MeshCentral are not used.

## Phase 4 acceptance

- 4.1 GitLab/GitHub recovery redundancy and cross-provider no-duplicate behavior: PASS.
- 4.2 Serverless replacement persistence for authorization/device state with Neon: PASS.
- 4.3 Live integration, concurrency/timeout evidence from Phase 3, failover/failback, watchdog reconnect and post-Vercel-redeploy command roundtrip: PASS.

The fixed ARA Phase 1–4 backlog is homologated complete. Future changes must preserve `vercel-neon` as the direct control plane, one canonical SYSTEM executor, durable job receipts, and the two independent private issue-queue recovery transports.