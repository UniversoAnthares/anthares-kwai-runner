# CF-02 production receipt historical recovery: safe nondeploying workflow
STATUS: RUNNING
AREA: cloudflare,github
DATE: 2026-10-26
RUN: pending
JOB: CF02-RECOVER-PROD-RECEIPT-20261026
COMMIT: 97871346f1d0ec11f7c8a978a00e659a8a362d4d
SUPERSEDES: none
LEASE_AREA: cf02-production-receipt-recovery-no-deploy
LEASE_OWNER: ChatGPT-CF02
LEASE_BASE: fix/cf02-prod-receipt-recovery-20261026@97871346f1d0ec11f7c8a978a00e659a8a362d4d
LEASE_SCOPE: only branch fix/cf02-prod-receipt-recovery-20261026, new recovery workflow .github/workflows/cf02-recover-receipt.yml, Python recovery tool and unit test, Test Hub append-only findings. No changes to preexisting production deploy workflow, Cloudflare Workers, publishers, queue state, credentials or existing receipt prior to independently verified GitHub Actions receipt-only job.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
CF02 R07.6 item 19 one-Worker staging real 503/rollback independently PROVEN in open PR #1402. Main deploy receipt still checked_at_utc=2026-10-19T23:45:51.943051+00:00 blob 47faf493a965be52cf57ea8780cc61f68510567f. Run 40283336472: production deployment, cleanup and health steps SUCCESS; only Save deployment receipt FAILED with HTTP409. Integrated CAS retry source main workflow blob 04029a3fc0622189d0f936d90ac0129fc2cf8d44, real GitHub 409 recovery proven on isolated QA run 40319550329. Newly executed Windows governance preflight CF02-RECEIPT-VALIDATION-20261026 exit 0; local governance manifest f6fc9ca59a96e451 and private GitHub manifest 2e28d54043d6bad1 diverge only in documented index; do not overwrite.

## FAILED_AVOIDED
Do not rerun cloudflare-central-deploy.yml: it redeploys the live Worker and invokes destructive-looking cleanup of old Kwai jobs despite receipt-only verification target. Do not change any publisher, D1/DO/KV, credentials or social queue. Do not fabricate fresh deploy metadata, conceal original workflow run failure or use a synthetic receipt.

## SUCCESS_SIGNAL
After reviewed normal PR merge, a separate GitHub Actions receipt-recovery workflow validates real GitHub API metadata AND logs for production run 40283336472 (actual Wrangler deploy, cleanup, health, TikTok boundary SUCCESS and save receipt HTTP409), reads production /health now, records an explicit verified_historical_recovery receipt in .github/cloudflare-cortes-status.json using CAS optimistic concurrency, and independently GETs the saved bytes. GitHub Actions job SUCCESS and new receipt on main with source_run provenance. No new Worker deploy or queue mutation.

## FAILURE_SIGNAL
If run lacks verified original deploy/cleanup steps, current controller health differs, contents permission or protected main rejects CAS, stop and leave original productive receipt unchanged. Record FAILED/PARTIAL without bypass or backfilled imaginary success.

## TEST_VALIDITY
This is NOT a new Cloudflare productive deploy E2E; it is a real provider write of an auditably recovered receipt for a prior confirmed productive deploy, without deployment or queue maintenance during recovery.
