# Diagnostic capture of production queue self-test server error
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: pending
JOB: queue-self-test-error-capture
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2137-queue-selftest-server500-partial.md proved v12 health, queue binding, exact Kwai OIDC transport and a server-side 500 from `/queue-self-test`.
FAILED_AVOIDED: this is not another acceptance attempt. It changes observability so curl always records the response body/status instead of exiting before printing the Worker's JSON error. Publication guard remains skipped; only isolated `__selftest__` state is used and cleaned by the Worker.
SUCCESS_SIGNAL: workflow prints `QUEUE_SELFTEST_HTTP=<status>` and a JSON response containing the explicit Worker `error` string needed to identify the failing invariant.
FAILURE_SIGNAL: response body/status cannot be captured or failure occurs before the endpoint responds.
TEST_VALIDITY: exact same allowlisted `kwai-real-publish.yml` OIDC identity and production v12 endpoint; no Android/media/publication path.

## Objetivo
Recover the exact production Durable Object selfTest exception so the next change attacks the observed cause rather than repeating the acceptance test blindly.
