# Lease renewal — Cloudflare control failover item 9
STATUS: RUNNING
AREA: cloudflare-control
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-0643-lease-cloudflare-control-failover-item9.md
LEASE_EXPIRES: 2026-10-06T11:45:00Z
BASELINE_PROVEN: commit 68cc5211897701747d0abfb6a52b9320eec9fc81 is on main; GitHub-hosted Control Plane Static Safety Validation run 37453329032 completed successfully; queue-fencing v16 invariants remain green.
FAILED_AVOIDED: do not reintroduce PC/local, Oracle or Google Compute; do not alter queue/fencing semantics or Durable Object migration.
SUCCESS_SIGNAL: deploy routing revision 2026-10-06-cloud-only-failover-r1, then production /health reports pc_fallback=false and that revision; /strategy exposes only cloud routes and retired executors; /failover-self-test returns ok=true with every scenario true including recovery; independent GitHub-hosted postdeploy validation passes.
FAILURE_SIGNAL: deployment changes queue/fencing version unexpectedly, retired executor appears in any route, recovery check fails, or postdeploy external validation fails.
TEST_VALIDITY: deploy exact main commit or a descendant containing it; if concurrent commit changes cloudflare-worker/src/index.js before deploy, rebase/re-audit rather than treating mismatch as product failure.