# Lease — GitLab watcher canonical Neon reservation handoff
STATUS: RUNNING
AREA: github-ci/gitlab-quota-ledger-handoff
DATE: 2026-10-27
RUN: none
JOB: none
COMMIT: 64717e1ddf07dc3ec862b45c6fd330e83a0ae840
SUPERSEDES: 20261027-gitlab-quota-handoff-live-dispatch-partial.md

Owner ChatGPT, same isolated controller PR. This lease covers only tools/gitlab_quota_watcher.py and .github/workflows/gitlab-quota-watcher.yml, for adding OIDC-authenticated shared Neon reservation before existing GitLab-to-GitHub dispatch. Expires 30 minutes after creation. No social posting, quota reset, credentials, provider priority or existing cancellation ownership changed.

BASELINE_PROVEN: PR #1521 already integrated; watcher has real GitLab status/cancel check and GitHub backup dispatch with independent quota. GitHub and GitLab current main file blobs match (script 8be70936132b179499a1ac790143b0da3d5255de; workflow ea09833dbb547dc2093a781de2363891da9d852b).
FAILED_AVOIDED: prevent cross-host double-dispatch, do not reserve if terminality is ambiguous, preserve existing protected Bitwarden GitLab token source.
SUCCESS_SIGNAL: watcher obtains GitHub OIDC only for exact scheduled workflow and atomically reserves project/pipeline in Vercel+Neon after remote terminal verification; only first owner can dispatch a successor.
FAILURE_SIGNAL: auth failure or DB unavailable cannot create a successor; no automatic bypass or retries.
TEST_VALIDITY: code deployment and subsequent naturally scheduled runs, no synthetic quota runs or manual publication tests.
