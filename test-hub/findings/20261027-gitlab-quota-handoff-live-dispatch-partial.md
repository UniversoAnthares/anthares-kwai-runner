# CORTES GitLab quota — live CI handoff (cancel-first guard)
STATUS: PARTIAL
AREA: github-ci/gitlab-quota-handoff
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504668947
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504668947/job/122190811506
COMMIT: 64717e1ddf07dc3ec862b45c6fd330e83a0ae840
SUPERSEDES: 20261027-lease-gitlab-quota-active-cancel-chatgpt.md, 20261027-lease-gitlab-quota-terminal-gate-chatgpt.md

## Operational implementation
PR #1521 merged to main. The installed 5-minute GitLab quota watcher now discovers quota-failed jobs in failed/canceled/active main pipelines, re-checks exact SHA and ref, and if a remote pipeline remains active and contains no other active jobs, requests actual GitLab API cancellation through GitLabPipeline and gates fallback on terminal status. Unknown or shared-job states block dispatch. Dry-run never cancels.

## Independent real execution (not simulated)
The actual push-triggered watcher run 40504668947 completed SUCCESS under main commit 64717e1... and emitted `ANTHARES_GITLAB_CREDENTIAL_SOURCE=BITWARDEN`, `DISPATCHED cortes pipeline=2994299294`, `clipper=NO_RECENT_MAIN_QUOTA_FAILURE`, `wordpress=NO_RECENT_MAIN_QUOTA_FAILURE`.
GitLab pipeline 2994299294 was already FAILED from ci_quota_exceeded before the watcher; no active remote cancellation was required or observed. The independent GitHub Actions run 40504693953 completed SUCCESS with `CORTES_GITLAB_CI_GITHUB_BACKUP=PASS`, without acquiring publishing authority. This establishes live GitLab-quota detection -> terminal-status authorization -> independent GitHub CI contract dispatch and completion. The fallback validates code/contracts; it does not publish media.

## Remaining
A real quota error while an exclusively owned GitLab pipeline is still active is required to prove a remote CANCEL receipt followed by terminal state. Shared active pipelines are protected by fail-closed logic. Other platforms' cancellation adapters and the CORTES Neon outbox consumer remain incomplete until their independent runtime principals and receipts are proven. CI success must never be promoted as production social publication.

## Lease closure
Close the two GitLab-quota leases above with this PARTIAL finding. No credential, production-posting, worker-role or payment mutation in this change. No test runs requested solely to manufacture an active quota incident.
