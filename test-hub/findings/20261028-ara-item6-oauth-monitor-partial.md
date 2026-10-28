# ARA item fixo 6 — OAuth runtime + monitor externo otimizados
STATUS: PARTIAL
AREA: anthares-remote / neon-idle-optimization / oauth-monitor
DATE: 2026-10-28
OWNER: ChatGPT GPT-6
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40783761059
JOB: Vercel dpl_8jsXuK3U3p6v4JD6rKwZgNZmvdgk
COMMIT: Vercel 16103054a90e1841971c502cbcc2507dbeee497e; GitHub main 82d1c420f3ec18d893809bcce78e8322a3757ec6
SUPERSEDES: optimization/ara-oauth-monitor-20261028:test-hub/findings/20261028-ara-oauth-monitor-lease.md ; test-hub/findings/20261028-ara-continuity-monitor-lease.md

## PROVEN
The live anthares-remote-primary Vercel deployment dpl_8jsXuK3U3p6v4JD6rKwZgNZmvdgk is READY with exact commit 16103054a90e1841971c502cbcc2507dbeee497e; production router.mjs blob 9029c4a3949f42516ba30981c2345f36a503f90a. Removed hot-path OAuth CREATE TABLE/INDEX during every cold start, while preserving INSERT ... ON CONFLICT DO NOTHING RETURNING jti for signed control and token replay. Neon main oauth primary key and job idempotency indexes independently confirmed. Public /health now performs one read-only presence query, no 4 UPDATE reap mutations or redundant DB test; 90s device presence TTL unchanged and authenticated lease/status continue to reap. Public live /health ok=true device_connected=true; OAuth metadata endpoints for Cloudflare, Vercel primary and secondary returned issuer, token/authorization endpoints, PKCE S256, ara.read and ara.write.

External GitHub ARA Authentication Continuity Monitor workflow changed through reviewed PR #1824 (merge 82d1c420f3ec18d893809bcce78e8322a3757ec6) to schedule lightweight public OAuth metadata checks every 30 minutes and original five-endpoint Neon/Cloudflare checks every 12 hours. Deep pass alone can close existing incident: shallow passes cannot falsely resolve a deep outage. Workflow remains enabled on default branch, no increase in provider costs. GitHub Actions run 40783761059 completed success on exact merge commit, decisive line:
{"healthy": true, "deep": true, "checks": {"mcp": {"http": 200, "ok": true}, "reserve_canonical": {"http": 200, "ok": true}, "reserve_standby": {"http": 200, "ok": true}, "primary": {"http": 200, "ok": true}, "secondary": {"http": 200, "ok": true}}}.

## STILL PENDING
Live C8 SYSTEM binary SHA256 4ffefc590d6825ba946373dbdc31f8d61c0b07932807f0c606a2275471fd609c still sends POST /v1/device/heartbeat every 60 seconds, and idle queue polls every 2 seconds. Preserving the 90-second connected TTL, git private issue-queue fallback and single-executor depends on authenticated, external presence/wake acceptance in item 5; do not merely lengthen heartbeat or TTL. Windows 30-second liveness and ~5-minute OAuth continuity guard also touch Neon; no safe replacement has been demonstrated yet. Windows remote execution intermittently aborts, WinRemote internal error and MeshCentral timed out; no local supervisor/cron/process changed. Neon OAuth table has about 61,580 expired mcp_signature records (~27MB total including other kinds), no destructive cleanup performed or authorized through SQL tooling. No proof of compute autosuspend or actual CU-hour savings until item 7.

## Rollback and safety
Previous primary production dpl_34YfhFrAn84AxPvgW3XRrrhu6EJd SHA 780290e39bf6dc56ee1af7503b37da9a5e219074; workflow pre-change blob 89a8ebac3e465b7703c31f29521b06b0b1e5b8a1. New deployment preserved Hostinger notifier and C8/Neon schema/Git queues unchanged. Do not claim fixed item 6 fully complete before C8 external presence/recovery/heartbeat and monitor cadence are jointly accepted in production.
