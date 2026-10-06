# Control-plane items 1–3 — definitively closed
STATUS: PROVEN
AREA: control-integration
DATE: 2026-10-06
RUNS: 37406236848; 37406595632
SUPERSEDES: test-hub/findings/20261006-lease-control-publisher-integration-qa.md
LEASE_CLOSED: 2026-10-06T02:57:00Z

## Item 1 — workflow/queue → fenced publisher
CLOSED. kwai_claim_job.sh authenticates with GitHub OIDC, verifies control v16/no-PC, atomically leases a Kwai job, rejects empty/incomplete/invalid leases, and exports canonical KWAI_QUEUE_JOB_ID + KWAI_LEASE_GENERATION + source interval and publisher payload. kwai_run_next_job.sh consumes that environment, validates kwai_real_publish_promotion_gate.py, then invokes kwai_publish.sh exactly once.

## Item 2 — UNCERTAIN → reconcile
CLOSED. kwai_run_next_job.sh enters kwai_reconcile_uncertain.sh only when publisher returns the explicit UNCERTAIN code 90, recovers MEDIA_SHA256 from the publication report, and never republishes as reconciliation. Reconciled confirmation is accepted only when the reconciler emits its positive terminal proof.

## Item 3 — integrated idempotency
CLOSED. Central claim excludes published/confirmed and uncertain jobs; lease_generation fences stale holders; canonical executor has one publisher invocation; uncertain path reconciles rather than re-publishes. Existing v16 production self-tests plus recovery/idempotency QA and dynamic executor QA cover terminal confirmed, uncertain-reconciled, uncertain-remains, pre-boundary failure and claim failure.

## Dynamic evidence
Run 37406595632:
- confirmed: SUCCESS
- publish-fails-before-boundary: SUCCESS
- uncertain-reconciled: SUCCESS
- uncertain-remains: SUCCESS
- claim-fails: SUCCESS

Run 37406236848: canonical ordering, single publisher invocation, uncertain-only reconciliation and fenced claim export static contract SUCCESS.

## Bug found and fixed during closure
Dynamic QA exposed that child-process exports from claim did not propagate to the canonical executor. Fixed by making the executor provide an explicit temporary GITHUB_ENV to kwai_claim_job.sh and sourcing it before the promotion gate. Subsequent 5/5 dynamic lifecycle matrix passed.

## Boundary
This closes control-plane engineering items 1–3. A real Kwai media Publish remains an external acceptance dependency on authenticated Android/session READY and is not evidence required to keep these control-plane items closed.
