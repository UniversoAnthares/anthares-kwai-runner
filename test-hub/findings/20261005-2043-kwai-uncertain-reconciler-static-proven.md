# Kwai UNCERTAIN reconciliation path proven fail-closed in source
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37395138497
JOB: 112049205004
COMMIT: 81c10a1021675fd1b615f8db9cec97c385ee839a
SUPERSEDES: test-hub/findings/20261005-2042-lease-kwai-uncertain-reconciler.md

BASELINE_PROVEN: specific account+title verifier and deterministic gallery matcher.
FAILED_AVOIDED: no generic freshness confirmation; no Profile unavailable=>absent inference; no call to kwai_publish_video or Publish from reconciliation.
SUCCESS_SIGNAL: dedicated reconcile path requires specific verifier evidence and central reconcile ACK; ambiguous result remains UNCERTAIN.
FAILURE_SIGNAL: any republish-capable call appears in reconciler or evidence-free reconcile is accepted.
TEST_VALIDITY: source/static integration proof only; control-plane deployment version may advance independently and must be re-pinned only after that deployment is PROVEN.

## Resultado
PROVEN in source snapshot. kwai_reconcile_uncertain.sh is observation-only: it invokes the specific publication verifier, requires KWAI_PUBLICATION_SPECIFICALLY_VERIFIED plus confirmation evidence, and then calls queue reconcile. Any verifier/controller failure exits UNCERTAIN. kwai_queue_state.sh reconcile requires evidence and only accepts a published+confirmed ACK.

## Evidência decisiva
Run 37395138497 / job 112049205004 completed success and emitted KWAI_UNCERTAIN_RECONCILE_STATIC_OK, KWAI_GALLERY_MATCHER_BEHAVIOR_OK, KWAI_STARTED_BEFORE_COMMIT_STATIC_OK and KWAI_PUBLISH_SAFETY_STATIC_OK.

## Consequência
Blind republish after UNCERTAIN is closed at the publication layer. Runtime reconciliation remains gated by a valid authenticated Profile. The concurrent control v15 source change is outside this proof until its production deployment is consolidated.
