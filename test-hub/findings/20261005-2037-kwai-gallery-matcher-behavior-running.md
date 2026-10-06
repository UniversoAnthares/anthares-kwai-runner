# Kwai gallery identity matcher behavioral validation
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2036-kwai-deterministic-gallery-static-proven.md.
FAILED_AVOIDED: no ACTION_SEND retry while MAIN precondition is unresolved; no real Publish; prior literal-newline harness defect is avoided by Python compilation before behavioral assertions.
SUCCESS_SIGNAL: isolated matcher accepts exactly one identity-bearing clickable tile and rejects both zero-match and multiple-match fixtures; lifecycle static signals remain green.
FAILURE_SIGNAL: generic tile is accepted, ambiguous duplicate identity is accepted, or lifecycle ordering regresses.
TEST_VALIDITY: pure XML/source behavioral test; no Android/session/publication claim.

## Objetivo
Upgrade deterministic selection evidence from grep-only static presence to executable behavior over controlled UI XML fixtures.
