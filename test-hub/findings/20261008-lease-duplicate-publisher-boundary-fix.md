# Lease duplicate publication model repair
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: 10245be7127aae89bb66d3bf745999ce157ac7f1
SUPERSEDES: none

BASELINE_PROVEN: syntax fixed, nine positive cases pass; duplicate publisher case fails.
FAILED_AVOIDED: no real publishing or duplicate test against production.
SUCCESS_SIGNAL: second publish rejected by model; all ten scenarios exit zero.
FAILURE_SIGNAL: any regression in other scenarios.
TEST_VALIDITY: Python compilation and ten explicit case runs.
Lease expires in 30 minutes.
