# Kwai publisher adapter aligned with production control v14
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394847995
JOB: 112048253338
COMMIT: 08f3263a413ae15e8ad56c94e596b174d51264c8
SUPERSEDES: test-hub/findings/20261005-2039-kwai-control-v14-adapter-running.md

BASELINE_PROVEN: production control v14 is PROVEN; Kwai started-before-commit and deterministic gallery matcher are PROVEN in source/behavioral validation.
FAILED_AVOIDED: stale v12 pin removed; v13 circuit-breaker regression remains superseded; arbitrary-version acceptance was not introduced.
SUCCESS_SIGNAL: exact v14 pin plus pc_fallback guard and all Kwai safety signals green.
FAILURE_SIGNAL: stale/arbitrary control version accepted or lifecycle safety regresses.
TEST_VALIDITY: source/static integration proof only.

## Resultado
PROVEN in snapshot. kwai_queue_state.sh now expects exactly 2026-10-05-queue-lease-renew-v14 and retains CONTROL_VERSION_MISMATCH plus pc_fallback=false enforcement.

## Evidência decisiva
Run 37394847995 / job 112048253338 completed success and emitted KWAI_GALLERY_MATCHER_BEHAVIOR_OK, KWAI_STARTED_BEFORE_COMMIT_STATIC_OK and KWAI_PUBLISH_SAFETY_STATIC_OK while asserting the exact v14 version string and absence of the stale v12 pin.

## Consequência
The control-plane version mismatch blocker is closed for Kwai publication. Remaining runtime blockers are authenticated/correct-account READY and real Android media-selection/composer evidence before the single canary.
