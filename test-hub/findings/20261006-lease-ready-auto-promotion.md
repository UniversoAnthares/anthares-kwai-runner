# Lease: READY -> one-job canary automatic promotion
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-06
LEASE_AREA: kwai-ready-auto-promotion
LEASE_EXPIRES: 2026-10-06T05:30:00Z
BASELINE_PROVEN: promotion gate + canonical executor + control items 1-5.
FAILED_AVOIDED: no Android/login mutation; no real Publish before READY; no generic GitHub runner pretending to have Android session.
SUCCESS_SIGNAL: executable readiness proof can promote exactly one canonical job only when authenticated READY evidence is present, otherwise fail-closed.
FAILURE_SIGNAL: missing/stale/mismatched READY can reach publisher, or promotion permits multiple jobs.
TEST_VALIDITY: static/dynamic contract tests only; irreversible publish remains disabled until external READY.
