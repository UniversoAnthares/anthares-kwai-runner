# Kwai production queue OIDC self-test
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: pending
JOB: isolated queue self-test
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2117-cloudflare-v12-production-proven.md; test-hub/findings/20261005-2124-lease-queue-production-selftest-oidc.md; `kwai-real-publish.yml` is already allowlisted by production v12 OIDC policy.
FAILED_AVOIDED: no real Kwai queue job is inserted or leased; no Android/emulator/media path runs; no publication branch runs on the dedicated push event. Worker `/queue-self-test` uses `platform=__selftest__`, UUID job IDs and deletes generated self-test jobs in finally.
SUCCESS_SIGNAL: run job emits `KWAI_PRODUCTION_QUEUE_OIDC_SELFTEST_OK` after public v12 health checks and `/queue-self-test` returns every required lifecycle invariant true.
FAILURE_SIGNAL: OIDC 401/403, HTTP failure, wrong v12 production identity, or any required self-test invariant is false.
TEST_VALIDITY: the run must originate from `.github/workflows/kwai-real-publish.yml` on the dedicated `.kwai-queue-self-test-trigger` push; guard/publication job must be skipped and no media inputs/actions may execute.

## Objetivo
Prove the production v12 queue and exact Kwai GitHub OIDC workflow identity together, using only the Worker's isolated Durable Object self-test namespace.
