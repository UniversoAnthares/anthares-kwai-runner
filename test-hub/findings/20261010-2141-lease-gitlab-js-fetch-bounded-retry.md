# Lease: GitLab JS QA checkout bounded retry
STATUS: RUNNING
AREA: gitlab-qa
DATE: 2026-10-10
OWNER: chatgpt-infra-automation-20261010-1740-ms
LEASE_UNTIL: 2026-10-10T22:10:00Z
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2934537419
JOB: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/jobs/17086600179
COMMIT: f8db5b10b446f3bc4a6da1cee9868785621d5dfb
SUPERSEDES: none

## Baseline and scope
BASELINE_PROVEN: GitLab QA branch !34 pipeline 2934537419 executed 6 of 7 jobs successfully on free Render custom runner; JS job 17086600179 failed after 300 seconds during get_sources, before node --check. PHP fast and extreme static jobs checked out same SHA successfully within seconds. Keep image node:22-bookworm-slim, actual JS checks and protected main unchanged.
FAILED_AVOIDED: no repeated full pipeline without causal change; no GitLab shared runner (ci_quota_exceeded); no re-run of proven PHP image smoke.
SUCCESS_SIGNAL: new JS job on same QA branch completes actual node --check and ANTHARES_JS_QA failed=0, with status success and checkout visible in trace.
FAILURE_SIGNAL: bounded checkout retry fails or job times out again, with exact stage recorded.
TEST_VALIDITY: new SHA, custom runner tag render-qa, real image and no skipped JS; fail-closed if job canceled/runner offline; record final outcome separately.

## Planned smallest change
On draft MR !34 branch only, bound stalled GitLab git fetch and enable one retry, preserving all JS checks, image, protected variables and artifacts. Do not merge or deploy production.
