# Kwai mobile authentication retry after SDK path failure
STATUS: RUNNING
AREA: kwai-login
OWNER: codex-kwai-mobile-auth-20261108
LEASE_UNTIL: 2026-11-08T20:43:03Z
HEAD_BASELINE: b9ee7bb7de2797fe7c8dd7cf9ba48ab780ce732d
WORKFLOW_BLOB: 083a50381977cf9be82f738a472584d2025a4698
GOVERNANCE_MANIFEST: 84905aefc5589d17
SUPERSEDES: 20261107-lease-kwai-login-live-handoff.md
BASELINE_PROVEN: Run 42435664183 booted hosted Android and validated the APK archive. Installation failed with adb not found, before noVNC or a vault write. The prior vault object was absent.
FAILED_AVOIDED: Expose the SDK platform-tools path to all bootstrap steps. No queue claim, publication, or local Android.
SUCCESS_SIGNAL: Live protected noVNC, exact Kwai UI identity, encrypted vault acknowledgement and two independent fresh Android restores.
FAILURE_SIGNAL: Install or handoff fails, identity or vault write fails, or either restore fails.
TEST_VALIDITY: Dispatch mobile_auth on main and verify all three hosted jobs. GitLab main differs and had no running or pending pipeline; no mirror or failover attempted.
