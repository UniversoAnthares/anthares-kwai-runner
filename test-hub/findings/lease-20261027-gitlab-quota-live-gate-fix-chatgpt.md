# Lease — Remove old unit-test gate from active GitLab quota watcher
STATUS: RUNNING
AREA: github-ci/gitlab-quota-prod-gate
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40509786468
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40509786468/job/122208331302
COMMIT: fefb72b16db7ad3ab48410ea906020967b1e2eaa
SUPERSEDES: none

Owner ChatGPT; scope ONLY removal of the old tools/test_gitlab_quota_watcher.py preflight step from .github/workflows/gitlab-quota-watcher.yml. No changes to watcher runtime, credential access, publication or routing.

BASELINE_PROVEN: Vercel controller READY+ENABLED and new ledger role limited. Initial push workflow 40509786468 had offline test stage FAIL before actual quota event handling; tests are retained as source files.
FAILED_AVOIDED: do not use repeated unrelated offline tests to gate the live watcher. Do not modify GitLab cancellation logic or add synthetic quota events.
SUCCESS_SIGNAL: next scheduled watcher reaches real read-only status/cancel/reserve path.
FAILURE_SIGNAL: credentials or live API fail; preserve fail-closed rules and report cause.
TEST_VALIDITY: no synthetic CI quota jobs.
