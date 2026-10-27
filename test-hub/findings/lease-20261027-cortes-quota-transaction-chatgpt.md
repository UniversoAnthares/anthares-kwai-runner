# CORTES-QUOTA-01 — isolated Neon schema verification lease
STATUS: RUNNING
AREA: architecture / cortes-quota-transaction-20261027
DATE: 2026-10-27
RUN: none
JOB: cortes-quota-neon-schema-isolated-20261027
COMMIT: runner main b9d6a66be04e1a3be74f15db4b90716bc0b6d800
SUPERSEDES: none

## BASELINE_PROVEN
CORTES canonical Neon has independent account/destination ledgers.
The quota decision library passed 18 GitHub Actions tests (run 40494211063).
Clipper main commit: 2c729cf59ef0bc3786076f60564c8bd3c95863ca.

## FAILED_AVOIDED
No uncontrolled 429 retries, shared-workflow cancellation,
production media publication, or false post confirmations.
Do not replace existing production queue tables.

## Test
Add separate quota cancellation event and outbox tables, verify constraints
in inactive isolated Neon QA branch qa-cortes-platform-quota-20261021.
Do not migrate production during this trial.

## SUCCESS_SIGNAL
CREATE TABLE succeeds and readback verifies two tables plus key
constraints. Existing CORTES publication ledger remains unchanged.

## FAILURE_SIGNAL
SQL error, missing constraint, concurrent lease collision, or
unexpected data changes.

## TEST_VALIDITY
Valid only on the named isolated QA branch with readback.
