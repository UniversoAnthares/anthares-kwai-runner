# Lease GitLab safe reconciliation
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: de1d047e3fa5591469ac14e56e8a209cf158f087
SUPERSEDES: none

BASELINE_PROVEN: seven repositories tree-equal, runner has four file differences; paused mirror workflow on GitHub.
FAILED_AVOIDED: no force push, no automatic mirroring without authenticated targets.
SUCCESS_SIGNAL: GitLab fast-forward to exact reviewed GitHub commit, identical trees and retained paused workflow.
FAILURE_SIGNAL: non-fast-forward or concurrent change; abort without rewriting history.
TEST_VALIDITY: compare refs and tree objects immediately after push.
Expires 30 minutes after creation. Scope only anthares-kwai-runner provider reconciliation.
