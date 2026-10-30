# QA-P0 controller hosted migration
STATUS: RUNNING
AREA: architecture/qa-p0
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: e796883c36f25c20fabad2fa522c5286a14a713b
SUPERSEDES: none

BASELINE_PROVEN: Controller executes only github-script JS, while runner is qa-p0-independent.
FAILED_AVOIDED: Preserve P0 issue deduplication, Windows executor, and publisher fences.
SUCCESS_SIGNAL: GitHub-hosted run of controller successful after merge.
FAILURE_SIGNAL: Workflow fails, cannot allocate hosted runner, or accidental dispatch duplication.
TEST_VALIDITY: Verify real main run, not just YAML change.
LEASE: controller workflow only, 2026-10-29, 30 minutes.
