# Lease: CHAT2 items 2-8 closure
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-06
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T06:00:00Z
BASELINE_PROVEN: v16 fenced publisher adapter; started-before-commit; executable UNCERTAIN reconciliation; deterministic gallery matcher; final SHA dedupe; control→publisher QA5.
FAILED_AVOIDED: no real Publish; no Android/login mutation; no competing control-plane mutation.
SUCCESS_SIGNAL: items 2-8 each have executable/static acceptance evidence and no unresolved implementation gap in the publisher boundary.
FAILURE_SIGNAL: a required invariant is absent, a stale holder crosses the boundary, media identity is ambiguous, or production wiring introduces a PC dependency.
TEST_VALIDITY: static/executable stubs for external Android/Kwai until independent AUTH READY; real publication is explicitly excluded from this lease.
