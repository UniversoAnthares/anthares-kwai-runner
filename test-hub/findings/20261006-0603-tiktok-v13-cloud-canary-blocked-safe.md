# TikTok v13 cloud canary round — BLOCKED after safe reconciliation
STATUS: BLOCKED
AREA: tiktok-publish
DATE: 2026-10-06
RUNS:
- https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37419627985
- https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37420390707
- https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37420617464
- https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37421339696
SUPERSEDES: test-hub/findings/20261006-0535-lease-tiktok-render-production-canary.md
SUPERSEDES: test-hub/findings/20261006-0600-lease-tiktok-github-30way-contender.md

## Proven this round
- Cloudflare GitHub OIDC authorization blocker is closed (protected central-session probe succeeded post-deploy).
- Render prepublish reached bootstrapped=true, identity_verified=true, ready_for_tiktok=true.
- v13 marked publication_started and Render then returned HTTP 502.
- Render event history proves the exact cause: server OOM-killed at the 512Mi free-plan memory limit at 05:46:46Z.
- The ambiguous v13 attempt was not retried. Independent /profile-inventory returned count=0; v13 was reconciled confirmed_absent and safely returned to queued.
- A serialized 15-way GitHub browser contender round produced no authenticated /upload contender.
- A 30-way parallel GitHub contender round also produced no authenticated /upload contender; no queue lease was acquired and no irreversible post occurred.

## Current blocker
The central TikTok session remains valid enough for Render identity/session tests, but the free Render 512Mi instance OOMs during the real browser publisher. GitHub-hosted browsers currently reject /upload authentication across the 30-way round. Retrying either unchanged mechanism is non-causal and should not be repeated.

## Safety state
No v13 post exists according to independent profile inventory. Central v13 is reconciled from UNCERTAIN to queued. No duplicate publication occurred.

## Next causal direction
A different free browser execution environment or a materially lower-memory publication implementation is required. Do not retry the same 512Mi Render publisher and do not rotate the central session solely because GitHub-hosted /upload rejects it.
