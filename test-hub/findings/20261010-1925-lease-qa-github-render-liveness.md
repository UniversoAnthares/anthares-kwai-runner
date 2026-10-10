# Lease QA — GitHub Render runner liveness
STATUS: RUNNING
AREA: qa-github-render-runner
DATE: 2026-10-10
RUN: none
JOB: none
COMMIT: 525014da0a1cd5cd960f201ffe6fa1d655ab9c99
SUPERSEDES: none

LEASE_OWNER: QA Anthares scheduled agent
LEASE_START_UTC: 2026-10-10T19:25:00Z
LEASE_EXPIRES_UTC: 2026-10-10T19:55:00Z
SCOPE: infra/github-runner-render/runner_service.py and focused liveness regression only
BASELINE_PROVEN: Current main file blob ec9737fb1d6a86f53d18493389d4ef326639e20b; source inspection confirms /health reads only a configured marker while run.sh can exit.
FAILED_AVOIDED: Prior marker-only health logic returned HTTP 200 after run.sh exit. Change readiness to a live subprocess poll rather than retrying deployment unchanged.
SUCCESS_SIGNAL: The exact branch SHA passes a regression asserting HTTP 200 with a live process and HTTP 503 with a terminated process; CI links recorded.
FAILURE_SIGNAL: Failed regression or CI, or any HTTP 200 with a dead runner.
TEST_VALIDITY: Import/test harness must not download or register a runner; test uses a mocked process and isolated /tmp ROOT.
CONCURRENCY: No production deployment, merge, queue/session mutation, or secrets; competing active lease for this scope takes precedence.
