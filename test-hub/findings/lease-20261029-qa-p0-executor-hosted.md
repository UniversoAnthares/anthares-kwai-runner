# QA-P0 hosted executor lease
STATUS: RUNNING
AREA: architecture/qa-p0-diagnostics
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: c2537fdadad687582438bb2e127f01b7d6672b2d
SUPERSEDES: none

BASELINE_PROVEN: controller GitHub-hosted run 40992225120 success. Executor remains qa-p0-independent with Windows PowerShell and one local Start-ScheduledTask branch.
FAILED_AVOIDED: do not touch active Windows scheduled producer, publisher state, media, or Neon CAS. No bypass of WordPress 403. No unapproved auto-publication.
SUCCESS_SIGNAL: hosted PR contracts pass and real executor workflow_dispatch validates an existing P0 and creates readback diagnostic without needing local files.
FAILURE_SIGNAL: hosted runner allocation/PowerShell failure or unapproved publisher action.
TEST_VALIDITY: PR test is only offline; verify production job and retained P0 open state.
LEASE: executor workflow, its read-only recovery playbook, and related safety test only; 30 minutes.
