# RET-CI-209 — GitLab isolated QA technical fallback lease
STATUS: RUNNING
AREA: retention-ci-isolated-gitlab
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40395690926
JOB: RET-CI-209-GITLAB-ISOLATED-20261026
COMMIT: GitHub PR #209 HEAD 0139b0978872535fabd0c9b761a0f1fa883c2fb0; GitLab main 1eab2129e71027a14e68407f52e86e643c0ada2b
SUPERSEDES: none

Owner ChatGPT. Lease <=30 minutes. Github Actions CI job 121827983246 failed pre-step (steps=[]), so code not tested on GitHub CI. Change of test executor is for synthetic code QA only; it is NOT a workaround for the previously rejected Google Drive upload. Do NOT replay any storage operation.

BASELINE_PROVEN: GitLab Anthares clipper main has divergent history, existing .gitlab-ci.yml includes publish and mirror stages, and branch qa/retention-209-ci-isolated-20261026 is absent. Test Hub governance preflight RET-CI-209-20261026 PASS.

FAILED_AVOIDED: Never trigger GitLab's production .gitlab-ci.yml. Create an atomic new branch commit from GitLab main including a replacement minimal .gitlab-ci.yml and exactly three QA source/test files copied byte-for-byte from GitHub PR #209. No port of other histories, no blind mirror of production files, no production changes, no secrets.

SUCCESS_SIGNAL: GitLab isolated branch pipeline logs `python -m unittest discover -s tests -p test_retention_v3_readonly.py` PASSED with 15 tests, no publish jobs. SHA/source comparison retained.
FAILURE_SIGNAL: any publish/mirror job, unexpected active production workflow, pipeline without real steps, CI quota issue or secrets exposure -> fail-closed and preserve branch only, no rerun identical failure.
TEST_VALIDITY: This is independent CI on matching QA source, not GitHub PR's native required check. Full PR #209 still requires GitHub CI eventually.
