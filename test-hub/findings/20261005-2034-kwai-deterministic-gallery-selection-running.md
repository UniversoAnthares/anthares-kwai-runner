# Kwai deterministic gallery selection hardening
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md; MediaStore identity is unique before composer selection; real publication remains quarantined.
FAILED_AVOIDED: direct ACTION_SEND run 37392541208 did not reach FSM_MAIN_REACHED because Launcher ANR recovery failed, so ACTION_SEND is not reused here. The current permissive gallery fallback selects candidates[0] without proving media identity and must not remain on a production-capable path.
SUCCESS_SIGNAL: prepare can select gallery media only when a clickable node exposes the exact media filename or its unique job/hash identity; ambiguous/no-match UI exits FAILED_SAFE before READY_TO_PUBLISH and before central started; static validation proves candidates[0] fallback is absent.
FAILURE_SIGNAL: any prepare path can reach READY_TO_PUBLISH after selecting an unidentified generic thumbnail, or static validation cannot prove fail-closed behavior.
TEST_VALIDITY: source/static validation only; no Android/login/publication claim is made. Real Publish remains quarantined.

## Objetivo
Remove the unsafe first-thumbnail fallback while preserving the proven started-before-commit lifecycle. Deterministic direct ACTION_SEND remains a separate runtime hypothesis blocked on a valid MAIN precondition.
