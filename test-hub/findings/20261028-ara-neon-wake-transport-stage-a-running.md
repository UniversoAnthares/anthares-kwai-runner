# ARA wake transport — isolated Stage A
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization
DATE: 2026-10-28
RUN: pending GitHub Actions CI
JOB: none
COMMIT: feature/ara-wake-hibernation-20261028 from caeb8fdc79a0f21441ed154899ad545a03b04ad3
SUPERSEDES: none

## BASELINE_PROVEN
Canonical C8 SYSTEM agent, Vercel+Neon primary and independent GitHub/GitLab
issue-queue transports are live. Current source performs 2-second idle polling
plus 60-second Neon heartbeat; leaseNext performs four reap updates per request.

## FAILED_AVOIDED
No existing Cloudflare DO was changed; shared DO write quota was exhausted
previously. No publication, secret rotation, quota burn, Neon DB mutation,
second process on user's PC, production deploy or primary routing change.

## SUCCESS_SIGNAL
GitHub Actions offline Node test outputs ARA_WAKE_NOTIFICATION_ONLY_CONTRACT=PASS;
WebSocket Worker and HMAC code are syntactically valid; unit tests cover bad
auth, foreign devices, payload tampering, stale timestamps, oversized payload
and canonical SHA-256 device fingerprint.

## FAILURE_SIGNAL
Any protocol/syntax or CI job failure, missing GitHub HEAD equivalence,
or unreviewed existing competing ARA mutation.

## TEST_VALIDITY
Only isolated source/protocol correctness is proven by such a CI run.
There is NO evidence yet of Cloudflare deployment, a live WebSocket,
notification delivery, Windows binary cutover or actual CU-hour saving.
