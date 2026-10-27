# CI-quota GitLab — lease for terminal cancellation fence
STATUS: RUNNING
AREA: gitlab-quota-watcher
DATE: 2026-10-27
RUN: none
JOB: none
COMMIT: 8beab0c822bc76352b8f5b7a11bd465f59c4ba63
SUPERSEDES: none

Owner: ChatGPT; isolated branch `fix/gitlab-quota-terminal-gate-20261027-chatgpt`. Lease expires 30 minutes after writing. No deployment, publication, credential changes or cancellation of unrelated jobs.

BASELINE_PROVEN: Current `tools/gitlab_quota_watcher.py` discovers quota failure in GitLab but dispatches alternative QA without a final exact-pipeline terminal receipt. The existing `tools/ci_quota_provider_adapters.py` supplies a GitLab pipeline cancellation/status API client.
FAILED_AVOIDED: active or uncertain pipeline must not cause overlapping QA dispatch; existing no-retry, 15-minute deduplication, credentials and publisher isolation preserved.
SUCCESS_SIGNAL: regression test demonstrates API exact-pipeline status read, cancel request before backup for a quota-confirmed still-running job, terminal verification and refusal on UNKNOWN/running/cancel denial; hosted regression run passes.
FAILURE_SIGNAL: any test fails, provider status is unavailable, or candidate rerun proceeds before pipeline termination.
TEST_VALIDITY: run executes tests in isolated branch without secrets, with API simulated; live API smoke is separately required for provider-level operational proof.

Current changes scoped to the read-only/QA GitLab quota watcher. The GitHub backup workflows themselves run only contracts, not social publication. Never cancel an unrelated job.
