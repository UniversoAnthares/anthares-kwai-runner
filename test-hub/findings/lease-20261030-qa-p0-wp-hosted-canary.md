# QA-P0 WordPress hosted authentication canary lease
STATUS: RUNNING
AREA: architecture/qa-p0
DATE: 2026-10-30
RUN: none
JOB: none
COMMIT: 65111bff8d34b998460bf939182fbc0dc3c199f6
SUPERSEDES: none

BASELINE_PROVEN: watchdog Windows route is healthy in run 41035659867 (WordPress observations=0, sources_failed=0), and cloud-alert job is independent on Ubuntu. Executor migrated to Ubuntu in PR #1969 and real run 41054962276. Existing cloud WP smoke code reports sanitized auth status without payload.
FAILED_AVOIDED: do not disable Windows QA before hosted authenticated 200, do not bypass 401/403, do not leak WP secrets, do not create P0 issues during a canary, do not dispatch media.
SUCCESS_SIGNAL: PR Ubuntu canary proves existing WP_QA_* secrets produce authenticated read-only JSON. Then migrate watchdog Windows route and verify real success in main.
FAILURE_SIGNAL: AUTH_MISSING, HTTP_401, HTTP_403, network error or untrusted payload. Preserve Windows route and cloud alert if canary fails.
TEST_VALIDITY: Only full production authenticated readback proves source; PR contract alone does not establish parity.
LEASE_SCOPE: .github/workflows/cortes-qa-p0-publication-watchdog.yml and one new Test Hub finding, 30 minutes.
