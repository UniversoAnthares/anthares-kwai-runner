# Lease: final control recovery + E2E closure
STATUS: RUNNING
AREA: control-final
DATE: 2026-10-06
LEASE_AREA: control-final-recovery-e2e
LEASE_EXPIRES: 2026-10-06T05:45:00Z
BASELINE_PROVEN: control v16; items 1-3 definitive; canonical executor dynamic 5/5.
FAILED_AVOIDED: no Android/login mutation; no real Publish; no kwai-control-dedupe-sha-final mutation.
SUCCESS_SIGNAL: integrated recovery matrix passes and final aggregate control-plane proof passes.
FAILURE_SIGNAL: stale/crashed holder can republish, uncertain restart can publish, or aggregate contract lacks a mandatory safety layer.
TEST_VALIDITY: executable simulated lifecycle + static/dynamic aggregate of current production contracts; real media acceptance remains external.
