# Lease cloudflare-control: deploy queue counter-reset correction as v13
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: v13-counter-reset
COMMIT: pending
SUPERSEDES: none

LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-06T00:42:00Z

BASELINE_PROVEN: test-hub/findings/20261005-2117-cloudflare-v12-production-proven.md; test-hub/findings/20261005-2140-queue-selftest-failure-counter-reset-failed.md identified the exact production bug through isolated OIDC self-test.
FAILED_AVOIDED: do not rerun acceptance against unchanged v12; do not alter unrelated routing/dedupe/confirmation behavior; version bump is mandatory so public acceptance distinguishes the repaired deployment.
SUCCESS_SIGNAL: source changes only the success-reset invariant plus explicit v13 identity/references; static safety/self-test source validation passes; production deploy reports the v13 version; isolated production `/queue-self-test` returns all invariants true through `kwai-real-publish.yml` OIDC.
FAILURE_SIGNAL: static regression, deploy mismatch, v13 not active, or any queue-self-test invariant remains false.
TEST_VALIDITY: deployment source must be current main after the causal patch and acceptance must query public workers.dev v13.

## Objetivo
Clear `disabled_until` on confirmed executor success, preserve all existing v12 safety invariants, promote the fix as an explicitly distinguishable v13 production Worker and rerun the isolated queue acceptance once.
