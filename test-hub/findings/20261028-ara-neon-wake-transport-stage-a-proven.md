# ARA wake transport — Stage A offline proof
STATUS: PROVEN
AREA: anthares-remote / neon-idle-optimization
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40760638379
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40760638379/job/123071294636
COMMIT: c79a6742f36a5c50c6274aef3b6a319fae243a95
SUPERSEDES: 20261028-ara-neon-wake-transport-stage-a-running.md

## Objective and result
Stage A: independent Worker protocol only, without production enablement.
GitHub Actions job 123071294636 completed SUCCESS. Verified syntax of both
Worker modules and Node protocol tests: accepted signed notification, bad MAC,
foreign device, oversized payload, time skew, token hash verification.
No Cloudflare Worker was deployed, no secret provisioned, no Windows agent
replaced, no change to Neon heartbeat or polling, no CU-hour savings claimed.

## Consequence
The offline HMAC/token/notifier interface is eligible for review. Stage B
notifier must remain default OFF and Stage C agent integration must not
cut over until independent wake delivery and a guaranteed recovery path
are proven; GitHub/GitLab issue-queue redundancy remains unchanged.
