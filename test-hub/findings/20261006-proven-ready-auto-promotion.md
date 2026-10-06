# READY automatic promotion barrier — proven
STATUS: PROVEN
AREA: kwai-publish
DATE: 2026-10-06
RUN: 37408701337
SUPERSEDES: test-hub/findings/20261006-lease-ready-auto-promotion.md
LEASE_AREA: kwai-ready-auto-promotion
LEASE_CLOSED: 2026-10-06T03:24:00Z

The canonical one-job executor now requires kwai_auth_ready_gate.py after queue/promotion validation and before its sole kwai_publish.sh invocation.

READY proof contract is fail-closed and requires JSON state=READY, account, observed_at and proof_id; optional expected-account equality is enforced; stale/future-invalid proof is rejected.

Five-way dynamic acceptance passed: valid accepted; missing rejected; non-READY rejected; account mismatch rejected; stale rejected. Static wiring additionally proves READY gate precedes the sole publisher invocation.

No Android/login mutation and no real media publication occurred. When the independent kwai-login agent produces a fresh authenticated READY proof, the canonical executor has no remaining human confirmation gate in this layer.
