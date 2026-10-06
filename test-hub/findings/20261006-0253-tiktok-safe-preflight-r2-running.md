# TikTok round-2 execution and adjacent audit
STATUS: RUNNING
AREA: tiktok-safe-preflight-r2
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37405053110
COMMIT: 423d11da516c7461d44a969e785503da06d5b28f

## Round 1 evidence
- control-health: PROVEN, anthares-control version 2026-10-05-queue-fencing-v16.
- session-status: PROVEN, bootstrapped=true, identity_verified=true, ready_for_tiktok=true.
- queue-health from new workflow_ref: EXPECTED AUTH FAILURE 401; confirms workflow_ref-specific Cloudflare allowlist.
- remaining round-1 jobs were still queued when round 2 was created; no duplicate publication or mutation.

## Round 2 five independent cases
1. Render session-status with valid OIDC.
2. Render session-test with valid OIDC.
3. Render session-status with deliberately invalid bearer, expected 401/403.
4. Cloudflare public health, expected 200.
5. Cloudflare queue health without bearer, expected 401/403.

No case calls enqueue, lease, started, complete or publish.

## Adjacent implementation already landed
Commit b2958039d186b3a2b4552b0dd4de76aa679ef21d:
- fixes curl --fail-with-body/-f incompatibility in the real canary path;
- disables the legacy workflow_dispatch publish job that attempted empty VIDEO_URL.

## Scheduler observation
At last check nine Actions runs were queued and zero were in_progress. The repository has substantial cross-agent runner backlog. Existing queued runs are not being duplicated.
