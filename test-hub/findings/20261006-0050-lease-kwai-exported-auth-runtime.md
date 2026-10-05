# Lease kwai-login exported auth runtime probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: pending
JOB: Android runtime probe
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-06T03:15:00-04:00
BASELINE_PROVEN: test-hub/findings/20261006-0048-kwai-auth-intent-contracts-proven.md
FAILED_AVOIDED: test-hub/findings/20261006-0028-declared-login-activities-not-exported.md; internal Activities are not direct-started.
SUCCESS_SIGNAL: exact exported URI leads to Login foreground, EditText, or explicit login/email/phone/password UI.
FAILURE_SIGNAL: all exact exported routes start/resolve without login UI.
TEST_VALIDITY: Kwai installed, each URI invocation logged, foreground and UI dump collected.
## Objetivo
Determine whether an exact exported Kwai auth URI reaches the internal login flow.
