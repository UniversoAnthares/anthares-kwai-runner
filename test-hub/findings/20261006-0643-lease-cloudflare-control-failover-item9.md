# Lease — Cloudflare control failover item 9
STATUS: RUNNING
AREA: cloudflare-control
DATE: 2026-10-06
LEASE_EXPIRES: 2026-10-06T11:10:00Z
BASELINE_PROVEN: queue-fencing v16 is deployed; pc_fallback=false; prior /failover-self-test proved Render -> GitHub -> null with local_retired=true; control items 1-5 are PROVEN.
FAILED_AVOIDED: do not reintroduce PC/local, Google Compute or Oracle; do not change queue/fencing semantics; do not count harness failures as failover failures.
SUCCESS_SIGNAL: production self-test proves healthy primary, Render-offline fallback to GitHub, total cloud outage -> null, stale heartbeat -> GitHub, circuit-breaker disabled Render -> GitHub, exhausted Render capacity -> GitHub, recovered Render -> Render, and injected local/oracle/google candidates are never selected; /health remains pc_fallback=false.
FAILURE_SIGNAL: any scenario selects local/oracle/google, recovery does not return to primary, or production health/fencing invariants regress.
TEST_VALIDITY: compare deployed /health version and current repository SHA before/after; if another Cloudflare deploy changes baseline during the run, mark INVALID and rebase instead of FAILED.

## Scope
Harden only failover selection/self-test and deploy/verify through the existing authorized Wrangler OAuth path. Preserve Durable Object queue semantics.