# X publisher module import fixed; Northflank preflight timeout after retry
STATUS: PARTIAL
AREA: x-publisher
DATE: 2026-11-23
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/45191313439
JOB: 137750101533
COMMIT: 9869c15fc4ccd1e304452954e86cf396f186a782
SUPERSEDES: 20261123-x-cloud-module-invocation-lease.md

## Baseline and fix
Owner directed immediate X publication restart. Existing issue #1002 [X-PUBLISH] was OPEN with zero comments. Hosted X browser readiness run #45187157011 confirmed X_GH_CLOUD_READINESS_ACCOUNT_VERIFIED=lucasyahn. First legacy X consumer attempt #45189665507 failed ModuleNotFoundError before any POST. PR #2753 merged in main, changing only the Python entrypoint to `python -u -m tools.x_cloud_issue_consumer`. Independent local read-only `python -B` import validation and branch command contract passed.

## Production result
One owner-authorized, idempotency-fenced attempt #45191313439 after the fix entered the consumer. The worker read-only preflight returned `X_QA_P0_ITEM_BLOCKED issue=1002 error=TimeoutError` after approximately 73 seconds; no X_POST_SUBMISSION_STARTED_V1/CONFIRMED record was created. Issue #1002 remains OPEN, zero comments, and there is no verified public X URL for this attempt. No second dispatch occurred. The legacy fallback workflow was restored to `disabled_manually`, and `ANTHARES_X_LEGACY_FALLBACK_ARM=0`. Cloud X primary remains disabled with `ANTHARES_X_AUTOPUBLISH=0`; this respects its existing hold. Northflank `/x/health` had previously returned HTTP 200, which is insufficient to prove the authenticated `/verify` service is responsive.

## Safe follow-up
Diagnose the independent Northflank authenticated `/x/verify` response, background worker session, capacity/quota and durable post-status for the exact issue key before any new real run. Preserve issue #1002, existing X posts, source media, owner account identity and global account mutex. Never infer success from a green job, never blind-post an UNCERTAIN item, never switch durable ledgers without full reconciliation. X source content is still eligible only after a fresh no-STARTED and remote idempotency check. No changes to other networks are authorized by this finding.
