# Lease: five heartbeat boundary probes
STATUS: RUNNING
AREA: qa
DATE: 2026-10-06
LEASE_AREA: kwai-heartbeat-qa2
LEASE_EXPIRES: 2026-10-06T04:00:00Z
BASELINE_PROVEN: immediate fenced renew + five independent safety probes.
FAILED_AVOIDED: no kwai-login, Android, media publication, anonymous YouTube, or production mutation.
SUCCESS_SIGNAL: five distinct boundary cases run concurrently and expose/fix any causal gap.
FAILURE_SIGNAL: child starts without valid initial lease, missing identity is tolerated, or periodic renew failure is not fail-closed.
TEST_VALIDITY: isolated shell contract with stub queue adapter.
