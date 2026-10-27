# Lease — documentation of new CI shared ledger
STATUS: RUNNING
AREA: github / ci-quota-docs
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504599465
JOB: 122190571791
COMMIT: 50128a042e7adf6c986701321454e6bdf7af070f
SUPERSEDES: none

Owned scope: append-only clarification in ci-hub/QUOTA_CANCEL_FIRST.md, no changes to integration states, dispatch or production runtime. Lease expires after this PR is closed.

BASELINE_PROVEN: PR #1522 merged; 6/6 hosted QA PASS; Neon isolated PostgreSQL QA transaction succeeded and rolled back with no residue, finding 20261027-ci-quota-postgres-real-qa-rollback-proven-chatgpt.md. Peer GitLab main and GitHub main had identical blob 29eefdd2a9c0f86baed160616561a604aa38f125.
FAILED_AVOIDED: documentation-only status must not claim live cancellation or production Neon migration.
SUCCESS_SIGNAL: main documentation mentions deployed-code versus non-deployed-schema explicitly.
FAILURE_SIGNAL: promoting any provider to operational or changing provider order without smoke evidence.
TEST_VALIDITY: static documentation diff only; hosted proof cited, no new job, token, schema or publication.
