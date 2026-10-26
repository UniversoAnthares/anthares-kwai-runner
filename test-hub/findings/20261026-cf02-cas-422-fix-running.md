# CF02 receipt CAS 422 stale SHA — isolated fix lease
STATUS: RUNNING
AREA: cloudflare, github
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40318947798
JOB: CF02-422-CAS-FIX-QA-20261026
COMMIT: 646cfd0a58bde8cdc41bcc392d9daa3636f93f8b
SUPERSEDES: test-hub/findings/20261026-cf02-real-provider-cas-running.md
LEASE_AREA: cf02-422-cas-source-fix-exclusive-qa
LEASE_OWNER: ChatGPT-CF02-CAS
LEASE_BASE: anthares-kwai-runner/evidence/cf02-real-provider-cas-qa-20261026@646cfd0a58bde8cdc41bcc392d9daa3636f93f8b
LEASE_SCOPE: only branch evidence/cf02-real-provider-cas-qa-20261026, modify the 422 handler in .github/workflows/cloudflare-central-deploy.yml and add isolated unit tests in tests/test_cloudflare_receipt_cas.py; QA branch workflow may read these sources. No main, no production receipt, no Cloudflare or publisher effects.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
PR #1346 merged main 00634f88955321cc94a3c480477a1001ff0b535d, existing 409 CAS retry/QA passed. Actual GitHub Actions on QA branch real provider returned HTTP422 `Invalid request.` after successful competitor commit: run #40318473908, verified in run #40318947798 with sanitized HTTP422 body. Competing writer successfully changed SHA; original receipt did NOT save. Single-point flaw is retry only on HTTP409, while provider returned HTTP422 under demonstrably stale SHA.

## FAILED_AVOIDED
No rerunning same 409-only test without causal fix, no production deploy, no workflow dispatch/Cloudflare token, no stale SHA writes on main. 422 is generic validation error and MUST NOT be treated as automatically retryable. Preserve production main until QA proves targeted behavior.

## SUCCESS_SIGNAL
After a 422, the CAS handler GETs actual current SHA. Retry only if SHA changed; unchanged SHA or a 403 fails closed. Real GitHub provider stale SHA conflict recovered, QA branch-only receipt created with exact source under test, tests pass. Merge to main only under safe controls avoiding auto-deploy and preserving rollback.

## FAILURE_SIGNAL
Any real QA 422 without changed SHA, retries exhausted, identity mismatch, persistent server error or provider DENIED -> fail/partial, no production rollout.

## TEST_VALIDITY
Proves real API concurrency in isolated QA branch; does not certify a new production Cloudflare deployment or CORTES ledger receipt.
