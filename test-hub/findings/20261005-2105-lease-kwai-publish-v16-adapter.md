# Lease kwai-publish control v16 fencing adapter
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2102-lease-kwai-publish-v15-closed.md
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T01:25:00Z

BASELINE_PROVEN: production control v16 2026-10-05-queue-fencing-v16; hub explicitly hands off kwai-publish client migration.
FAILED_AVOIDED: v15 client lacks lease_generation and renew; do not publish or touch active kwai-login Agent lease.
SUCCESS_SIGNAL: exact v16 pin; holder mutations carry current lease_generation; renew supported; stale generation cannot mutate; existing publication/reconcile invariants remain green.
FAILURE_SIGNAL: missing generation on started/complete/fail/renew, stale generation accepted, or safety regression.
TEST_VALIDITY: source/static + contract fixtures, no real Publish.

## Objetivo
Migrate CHAT 2 queue adapter to the production v16 fencing contract before runtime publication.
