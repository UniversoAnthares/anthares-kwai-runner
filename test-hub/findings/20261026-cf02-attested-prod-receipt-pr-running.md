# CF-02 verified real production deployment receipt via normal protected-main PR
STATUS: RUNNING
AREA: github, cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40329764097
JOB: 121595807899
COMMIT: 3c75c32b9a474e134a372f8f9c648af279009660
SUPERSEDES: test-hub/findings/20261026-cf02-recovery-log-auth-running.md
LEASE_AREA: cf02-production-receipt-recovery-no-deploy
LEASE_OWNER: ChatGPT-CF02
LEASE_BASE: fix/cf02-attested-prod-receipt-pr-20261026@3c75c32b9a474e134a372f8f9c648af279009660
LEASE_SCOPE: only branch fix/cf02-attested-prod-receipt-pr-20261026, append-only findings and .github/cloudflare-cortes-status.json. Do not call Cloudflare deploy, /cortes/maintenance/cleanup-legacy-kwai, modify queues, secrets or other agents. Receipt recovery must follow existing branch rules by reviewed normal PR, not bypass the GitHub ruleset.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
- Actual production deploy GitHub Actions #40283336472/job 121441273566: source 26ae1bdb3ba1095ab8b0230893134053804b4709; WRANGLER_DEPLOY_OK=1; CORTES_LEGACY_CLEANUP_REMOVED=0; CORTES_LEGACY_CLEANUP_PROTECTED=6; CONTROL_HEALTH_OK=1; TikTok boundary SUCCESS. The save receipt step alone failed HTTP409.
- After integrated HTTP409 CAS retry PR #1346, QA provider conflict real #40319550329 SUCCESS.
- No-deploy recovery code PR #1448 integrated f5cf30ee... and safe cross-host log redirect #1450 integrated 3c75c32b...; prod run #40329764097 proved live source run metadata, original job steps/logs and current /health; the last CAS PUT to main failed HTTP409 even on retry.
- Root cause confirmed GitHub REST rulesets/25443611 `proteger-main`: active branch protection, requires pull_request for default branch. This is NOT a CAS stale SHA error. Do not weaken protection. No receipt was changed during failed attempts (blob SHA 47faf493a965be52cf57ea8780cc61f68510567f).
- Live production health at 2026-10-26T13:23:51.244Z: ok=true, version=2026-10-17-physical-android-v18, persistent_state=true, queue_bound=true, pc_fallback=false. Preflight ARA CF02-RECEIPT-VALIDATION-20261026 exit0, GitHub governance manifest 2e28d54043d6bad1, Windows local f6fc9ca59a96e451; no sync overwrite.

## FAILED_AVOIDED
No blind rerun of deploy+queue cleanup, no weakening main ruleset, no token privilege increase, no fabricated new Cloudflare deployment, no repeating direct GitHub Contents main PUT known to 409 behind required PR. Any conflict/failed check abort and preserve existing receipt.

## SUCCESS_SIGNAL
Normal reviewed GitHub PR merges evidence-backed historical production receipt into protected main, citing exact source run/job/head SHA, source cleanup proof, live health verification, `receipt_mode=verified_historical_recovery`, no new deploy/no queue mutation; independently GET same bytes and new blob SHA on main.

## FAILURE_SIGNAL
If PR cannot merge under rules or main target changed, do NOT bypass; leave receipt untouched and document actual blocker.

## TEST_VALIDITY
Recovery of true prior production deployment evidence, not new production deploy E2E. There are no mutations to Cloudflare Worker, queue or social publishers.
