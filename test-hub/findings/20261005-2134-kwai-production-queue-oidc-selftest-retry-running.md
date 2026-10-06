# Kwai production queue OIDC self-test after curl harness repair
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: pending
JOB: isolated queue self-test
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: production v12 is active; `kwai-real-publish.yml` is allowlisted; Worker `/queue-self-test` uses isolated `__selftest__` jobs and cleans them.
FAILED_AVOIDED: test-hub/findings/20261005-2132-kwai-production-queue-selftest-curl-invalid.md. The POST command now uses `curl --fail-with-body -sS`, removing the incompatible `-f` shorthand. Guard/publication remains skipped on the dedicated push event.
SUCCESS_SIGNAL: `KWAI_PRODUCTION_QUEUE_OIDC_SELFTEST_OK` after production v12 health validation and every required Worker self-test invariant is true.
FAILURE_SIGNAL: OIDC rejection, HTTP error from `/queue-self-test`, or any required invariant false.
TEST_VALIDITY: run must originate from `.github/workflows/kwai-real-publish.yml`; guard job skipped; no Android/media/publication path invoked.

## Objetivo
Repeat only the previously invalid production OIDC queue self-test with the curl command repaired.
