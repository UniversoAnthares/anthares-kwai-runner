# Lease: post-commit crash/restart no-republish QA
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
LEASE_AREA: kwai-crash-recovery-qa
LEASE_EXPIRES: 2026-10-06T03:20:00Z
BASELINE_PROVEN: control v16 fencing; started-before-commit; UNCERTAIN observation-only reconciler.
FAILED_AVOIDED: no real Publish; no Android/login mutation; no active publisher mutation.
SUCCESS_SIGNAL: simulated irreversible commit followed by crash yields UNCERTAIN and restart cannot call prepare/commit/publish.
FAILURE_SIGNAL: any restart path invokes publication for an UNCERTAIN job.
TEST_VALIDITY: executable state-transition harness with call ledger.
SCOPE: dedicated tests/workflow/findings only.
