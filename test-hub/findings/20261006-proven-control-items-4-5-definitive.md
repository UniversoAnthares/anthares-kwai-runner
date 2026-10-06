# Control-plane items 4–5 — definitive closure
STATUS: PROVEN
AREA: control-final
DATE: 2026-10-06
RUNS: 37407204287; 37407207707
SUPERSEDES: test-hub/findings/20261006-lease-control-final-recovery-e2e.md
LEASE_CLOSED: 2026-10-06T03:05:00Z

## Item 4 — integrated failover/recovery
CLOSED. Final Recovery Integration QA5 passed 5/5:
- crash before publication_started returns work to queued and allows fenced reclaim with higher generation;
- crash after publication_started transitions to UNCERTAIN and blocks reclaim;
- stale holder cannot publish after a newer generation is acquired;
- restart of UNCERTAIN cannot invoke publication a second time;
- confirmed-absent reconciliation can safely requeue, and the next claim receives a higher generation.

RUN 37407204287.
JOBS: 112087293825; 112087293973; 112087293975; 112087294073; 112087294093.

## Item 5 — final control-plane end-to-end proof
CLOSED for the control-plane boundary. Aggregate proof validates the current repository chain in one run:
Worker v16; atomic lease generation; stale-generation fencing; UNCERTAIN state; reconcile endpoint; GitHub OIDC claim; generation propagation; promotion gate; heartbeat renew; started acknowledgement; complete acknowledgement; uncertain marking; publication-specific reconcile evidence; exactly one publisher invocation in canonical executor; uncertain-only reconciliation; queue-state generation contract.

RUN 37407207707.
JOB: 112087304133.
SIGNAL: FINAL_CONTROL_PLANE_E2E_CONTRACT_OK.

## Scope conclusion
Control-plane original items 1–5 are now CLOSED/PROVEN. No PC runtime dependency is introduced. No real Android/Kwai Publish was executed by these closure tests. Real-media acceptance remains a separate external session/login acceptance boundary and does not reopen control-plane items 1–5 unless that acceptance reveals a new control-plane defect.
