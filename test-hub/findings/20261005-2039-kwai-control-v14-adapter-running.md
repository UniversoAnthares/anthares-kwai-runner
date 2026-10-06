# Kwai queue adapter align to production control v14
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: production control v14 version 2026-10-05-queue-lease-renew-v14 is PROVEN with queue renew, single-job claim and circuit-breaker reset; Kwai started-before-commit lifecycle is statically PROVEN.
FAILED_AVOIDED: v13 failure_counter_reset_failed is superseded by v14; publisher must not keep stale v12 version pin and must not weaken version checking to arbitrary versions.
SUCCESS_SIGNAL: queue adapter pins the exact proven v14 version, still requires pc_fallback=false, and full Kwai safety validation remains green.
FAILURE_SIGNAL: adapter accepts stale v12/arbitrary version, loses pc_fallback guard, or lifecycle validation regresses.
TEST_VALIDITY: source/static integration proof; no real Publish.

## Objetivo
Align the Kwai publication adapter with the now-PROVEN production control plane v14 without weakening fail-closed version validation.
