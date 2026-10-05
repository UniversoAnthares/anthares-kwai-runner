# Kwai publish lifecycle hardening validation
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: static validation
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2058-lease-kwai-publish-started-verifier-hardening.md; queue confirmation invariants are PROVEN in snapshot; real publication remains quarantined.
FAILED_AVOIDED: malformed workflow commit 071c53e is not reused; no Android Publish action; no generic recency marker accepted; no stale Worker call is executed by this static test.
SUCCESS_SIGNAL: workflow emits `KWAI_STARTED_BEFORE_COMMIT_STATIC_OK` and `KWAI_PUBLISH_SAFETY_STATIC_OK` after bash syntax, Python compile, required guard checks, and ordering assertions all pass.
FAILURE_SIGNAL: syntax/compile failure, missing invariant, or ordering assertion failure.
TEST_VALIDITY: this run executes source/static checks only; green result cannot be classified as real publication/authentication proof.

## Objetivo
Validate the new prepare -> central started -> commit -> specific verification -> central complete ordering and fail-closed verifier contract before any runtime media-ingress probe.
