# GitLab quota watcher — live cancellation hardening
STATUS: RUNNING
AREA: github-ci/gitlab-quota-handoff
DATE: 2026-10-27
RUN: none
JOB: none
COMMIT: b6f4c0ebe9d89c90b81567cbfb671ca5b0b0226f
SUPERSEDES: none

## Change ownership and boundaries
Owner: ChatGPT, isolated branch `fix/gitlab-live-cancel-on-quota-active-20261027-chatgpt`; lease expires 30 minutes after creation. Read-before-write: GitHub main watcher blob f842ece47ddbebfdeb9d4d915a78824ed9b800d9, GitLab main peer identical blob. No other source files assigned. Preserve producer/pub workloads, no manual cancellation or new runs.

BASELINE_PROVEN: scheduled `gitlab_quota_watcher.py` currently lists ONLY already-FAILED main pipelines and automatically dispatches QA fallback.
FAILED_AVOIDED: cancellation of an unrelated still-running job or a whole shared pipeline; fallback while a pipeline remains active or an event is uncertain.
SUCCESS_SIGNAL: main watcher can recognize recent quota failure in active or canceled pipelines, request cancellation only for a pipeline with no unrelated active jobs, verify terminal state, then hand off to QA-only independent route.
FAILURE_SIGNAL: any cross-provider duplicate, cancellation of non-owned running jobs, unknown outcome dispatched, security error categorized as quota.
TEST_VALIDITY: existing offline watcher contract, no new live test job; evidence must distinguish deployed code from observed real quota transition.
