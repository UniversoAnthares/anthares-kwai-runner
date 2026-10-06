# Active lease index and conflict audit — PROVEN
STATUS: PROVEN
AREA: test-hub / coordination
DATE: 2026-10-06
RUN: 37403196894
JOB: 112074793759

The reusable Hub Active Lease Index completed successfully. It separates active leases from expired RUNNING findings and the workflow now also computes active_area_conflicts in its JSON artifact.

Observed at execution: ACTIVE_LEASE_COUNT=11; EXPIRED_RUNNING_COUNT=17.
Artifact: hub-active-leases.json.
Historical findings remain append-only; consumers should use expiry-aware active state.
