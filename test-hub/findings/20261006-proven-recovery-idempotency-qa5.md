# Recovery / idempotency QA5 — PROVEN
STATUS: PROVEN
AREA: control-integration
DATE: 2026-10-06
RUN: 37405505384
JOBS: 112082067291; 112082067530; 112082067536; 112082067547; 112082067571

Five isolated integration invariants passed:
- UNCERTAIN is not republished.
- expired unstarted work can be reclaimed.
- reclaim increments generation and fences old holder.
- confirmed/published work cannot be reclaimed.
- reconciled confirmed work remains terminal.

No real publication or Android/login mutation.
