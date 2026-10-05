# Kwai Profile dynamic-module loading must never be treated as confirmed absence
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: read-only code/evidence audit
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2041-qa-kwai-started-handshake-gap.md; current state-driven Profile logic.
FAILED_AVOIDED: previous Profile probes failed during unstable traversal; this finding does not reuse them as publication evidence and does not publish.
SUCCESS_SIGNAL: existing Profile navigation code explicitly recognizes `resource downloading` / dynamic module loading and waits before concluding auth controls are absent.
FAILURE_SIGNAL: verifier/reconciler interprets loading/timeout as confirmed post absence and makes a retry eligible.
TEST_VALIDITY: read-only invariant derived from current Profile state handling; no live post assertion.

## Resultado
Current Profile navigation explicitly treats `resource downloading` / `access to all the features when` as a dynamic-feature loading state, waits in bounded loops, and only inspects controls after that state clears or a controlled reopen. Publication verification currently has a shorter independent loop and does not model this loading state.

## Consequência
For publication reconciliation, Profile loading, module timeout, navigation ambiguity, or inability to reach the Profile grid must preserve `UNCERTAIN`. `confirmed_absent=true` is forbidden from those states. A retry may be released only after a stable Profile/account identity is positively established and the relevant publication is positively proven absent by a stronger criterion. The verifier should expose `PROFILE_LOADING`, `PROFILE_READY`, and `PROFILE_UNAVAILABLE` separately.
