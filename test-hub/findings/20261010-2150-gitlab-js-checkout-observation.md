# GitLab QA JS checkout observation
STATUS: PARTIAL
AREA: gitlab-qa
DATE: 2026-10-10
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2934537419
JOB: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/jobs/17086600179
COMMIT: f8db5b10b446f3bc4a6da1cee9868785621d5dfb
SUPERSEDES: test-hub/findings/20261010-2141-lease-gitlab-js-fetch-bounded-retry.md

Six of seven jobs succeeded. The JS job timed out after 300 seconds while fetching the repository, before executing JavaScript checks. Three successful jobs checked out the same commit. The isolated recovery branch was created. The attempted CI edit was blocked by connector safety checks. No code changes or production deploy occurred. Preserve the draft merge request. Next: implement a bounded checkout retry in reviewed CI, then verify actual JS syntax checks before merging.
