# Lease — persist accepted GitHub quota fallback receipts
STATUS: RUNNING
AREA: github-ci/gitlab-quota-dispatch-receipt
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510130758
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510130758/job/122209533226
COMMIT: eccfdc3129b54141be342237727b3582d8864fc9
SUPERSEDES: none

Owner ChatGPT. Scope: add api/gitlab-ack.mjs to isolated Vercel quota controller and update tools/gitlab_quota_watcher.py after successfully acknowledged GitHub dispatch. No retries, no publication, no modifications to other workflows. Lease expires after 30 minutes.

BASELINE_PROVEN: real GitLab pipeline 2994547840 became Neon FALLBACK_RESERVED via Vercel and dispatched GitHub run 40510154187 SUCCESS. Ledger manually reconciled to FALLBACK_CONFIRMED with exact SHA and generation CAS.
FAILED_AVOIDED: 204 GitHub workflow_dispatch has no remote run_id; never claim confirmed success from 204. Record only SUBMITTED; confirmation remains a separate independent step.
SUCCESS_SIGNAL: next real quota dispatch records FALLBACK_SUBMITTED after GitHub 204 without possible duplicate dispatch.
FAILURE_SIGNAL: 4xx/5xx ambiguous receipt remains quarantine and cannot trigger retry.
TEST_VALIDITY: observe naturally scheduled workflow only; no artificial quota incident or publishing.
