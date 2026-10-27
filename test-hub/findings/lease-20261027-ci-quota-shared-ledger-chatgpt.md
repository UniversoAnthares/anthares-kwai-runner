# Lease — CI quota cross-host fenced ledger
STATUS: RUNNING
AREA: github / ci-quota-ledger
DATE: 2026-10-27
RUN: none
JOB: independent QA on authorized Windows
COMMIT: 8beab0c822bc76352b8f5b7a11bd465f59c4ba63
SUPERSEDES: none

Owner: ChatGPT. Lease scoped to NEW files tools/ci_quota_neon_ledger.py, tests/test_ci_quota_neon_ledger.py and db/migrations/20261027_ci_quota_fenced_ledger.sql. Expires 30 minutes after initial commit. No writes to current provider adapters, real workflows, production Neon, running publishers or credentials.

BASELINE_PROVEN: PR #1503 merged, SQLite ledger single-host. Neon already has CORTES quota outbox but CI cross-host adapter is absent.
FAILED_AVOIDED: never promote a single-host JSON/SQLite ledger to multi-cloud; never re-enqueue with unknown remote termination. Keep new adapter opt-in with no DB access at import time.
SUCCESS_SIGNAL: owner and generation compare-and-swap pass isolated tests; second observer cannot claim or enqueue same attempt; stale lease fails closed.
FAILURE_SIGNAL: stale owner update succeeds or duplicate claim returns true.
TEST_VALIDITY: simulated PostgreSQL transactions cannot prove production DB, provider cancellation or callback wiring. Require explicit deploy and real terminal receipts.
