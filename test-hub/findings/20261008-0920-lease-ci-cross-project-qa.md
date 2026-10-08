# Cross-project CI repair lease
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-kwai-runner/-/pipelines/2926659987
JOB: 17031764384
COMMIT: a15dd5838f873de83360464c379752ab7dc677aa
SUPERSEDES: none

BASELINE_PROVEN: all three audited repositories are byte-identical and share the same HEAD across GitHub/GitLab after convergence merges. Provider-router tests pass and local structural audit passes.
FAILED_AVOIDED: anonymous clone of private GitHub anthares-clipper failed in GitLab CI; do not retry anonymous private clone.
SUCCESS_SIGNAL: kwai GitLab pipeline clones the sibling GitLab Clipper repository with CI_JOB_TOKEN and all jobs pass.
FAILURE_SIGNAL: scoped job-token authentication fails or any validation job regresses.
TEST_VALIDITY: target Clipper allowlists only the kwai-runner project; no PAT is exposed to CI; current file and HEAD must be re-read before mutation.
Lease expires 30 minutes after acquisition.
