# Lease tiktok-publish clear stale v2 reservation and repair v3 fencing
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: tiktok-publish
EXPIRES: 2026-10-06T04:20:00Z

BASELINE_PROVEN: v2 publication was reconciled absent by independent profile check; v3 media preparation is proven, but v3 never reached publish because the control lease returned stale v2.
FAILED_AVOIDED: do not publish v2 again; do not create a third concurrent canary. The causal defect is stale v2 remaining claimable in the central queue plus v3's insufficient stale-job reconciliation.
SUCCESS_SIGNAL: one controlled run clears the reconciled-absent v2 using its current lease generation, acquires v3, passes the no-publish memory gate, and either reaches publish or produces a new causal failure.
FAILURE_SIGNAL: stale v2 cannot be fenced safely, another job is claimed, or v3 reaches publication without the prepublish safety gates.
TEST_VALIDITY: central queue responds; v2 absence is already user-confirmed; v3 has not crossed publication_started in the failed runs.

## Objective
Repair the v3 canary's queue fencing so the already-reconciled-absent v2 cannot block acquisition of v3. Preserve fail-closed behavior and do not issue a publication retry for v2.
