# Lease kwai-login declared activity probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388231997
JOB: single Android activity probe
COMMIT: a0cda10864a4c165d28482989bed90dc3d17d71d
SUPERSEDES: none
EXPIRES: 2026-10-06T01:45:00-04:00

BASELINE_PROVEN: test-hub/findings/20261006-0018-kwai-manifest-login-components-proven.md
FAILED_AVOIDED: test-hub/findings/20261006-0002-kwai-direct-login-no-runtime-targets.md; use exact Manifest names rather than Tiny* guesses. No onboarding/profile matrix is used.
SUCCESS_SIGNAL: at least one declared login Activity starts and UI dump contains EditText or login/email/phone/password/auth controls attributable to that Activity.
FAILURE_SIGNAL: every selected declared Activity is rejected or starts without any login/auth UI signal.
TEST_VALIDITY: Kwai install succeeds; adb package exists; each am start result and foreground component are logged; UI dump parse failure is explicit.

## Objetivo
Test exact declared Kwai login Activities directly in one Android job.

## Consequência
Serialize kwai-login mutations until this probe closes.
