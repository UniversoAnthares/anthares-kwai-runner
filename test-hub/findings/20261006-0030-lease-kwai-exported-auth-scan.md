# Lease kwai-login exported auth entrypoint scan
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: pending
JOB: static manifest scan
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-06T02:15:00-04:00

BASELINE_PROVEN: test-hub/findings/20261006-0018-kwai-manifest-login-components-proven.md
FAILED_AVOIDED: test-hub/findings/20261006-0028-declared-login-activities-not-exported.md; do not direct-start internal Activities.
SUCCESS_SIGNAL: manifest identifies at least one exported or intent-filtered auth/account/login/profile Activity/alias suitable as an external entrypoint.
FAILURE_SIGNAL: no auth-related external entrypoint is declared.
TEST_VALIDITY: aapt runs and full manifest is parsed.
## Objetivo
Find a legal external entrypoint into the app's internal authentication flow.
## Consequência
Only candidates from this scan may be considered for the next Android probe.
