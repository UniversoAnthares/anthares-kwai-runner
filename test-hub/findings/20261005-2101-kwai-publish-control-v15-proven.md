# Kwai publication layer aligned to production control v15
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396695985
JOB: 112054272757
COMMIT: cd3d2428f3336c265ed8c3ef18d950833f4366c8
SUPERSEDES: test-hub/findings/20261005-2100-lease-kwai-publish-v15-alignment.md

BASELINE_PROVEN: production control v15 2026-10-05-queue-heartbeat-renew-v15.
FAILED_AVOIDED: stale v14/v12 pins removed; active kwai-login Android Agent lease untouched; no real Publish.
SUCCESS_SIGNAL: exact v15 pin and all existing publication safety signals green.
FAILURE_SIGNAL: stale/arbitrary version accepted or lifecycle/reconcile regression.
TEST_VALIDITY: source/static integration proof.

## Resultado
PROVEN. CHAT 2 is aligned to production v15. The adapter requires the exact v15 version and retains pc_fallback=false, started-before-commit, deterministic media identity, specific verifier and fail-closed UNCERTAIN reconciliation.

## Evidência decisiva
Run 37396695985 / job 112054272757 emitted KWAI_GALLERY_MATCHER_BEHAVIOR_OK, KWAI_UNCERTAIN_RECONCILE_STATIC_OK, KWAI_STARTED_BEFORE_COMMIT_STATIC_OK and KWAI_PUBLISH_SAFETY_STATIC_OK.

## Consequência
The publication layer is ready for runtime prepare-only validation as soon as the independent kwai-login Android Agent reaches READY with correct account identity.
