# Lease: control → publisher integration QA
STATUS: RUNNING
AREA: control-integration
DATE: 2026-10-06
LEASE_AREA: control-publisher-integration
LEASE_EXPIRES: 2026-10-06T05:30:00Z
BASELINE_PROVEN: Cloudflare v16 fencing; kwai publisher heartbeat/fencing; QA6 10/10.
FAILED_AVOIDED: no real Publish, no Android/login mutation, no anonymous YouTube path.
SUCCESS_SIGNAL: ten isolated integration/recovery/idempotency contracts pass and promotion boundary is machine-checkable.
FAILURE_SIGNAL: publisher can start without canonical job/generation, stale holder can cross boundary, or confirmed/uncertain jobs can be duplicated.
TEST_VALIDITY: stubs/simulated lifecycle only; no claim of real end-to-end publication.
