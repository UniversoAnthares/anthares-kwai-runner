# ARA item 8 — Heartbeat and presence SQL optimized in production
STATUS: PROVEN
AREA: anthares-remote / neon-idle-optimization / queue-read-presence
DATE: 2026-10-28
RUN: Vercel deployment dpl_H3k2Fuy3ee9A2px9AGcwQwVTusdF
JOB: authenticated signed gateway session_status, production Neon read-only SQL
COMMIT: d6204db9f0800e7a83275821bafc63a1065a4f1f
SUPERSEDES: 20261028-ara-item8-heartbeat-presence-running.md

## Change / scope
The signed MCP status route at anthares-ara-vercel-reserve now uses a single parameterized, read-only PostgreSQL SELECT joining device heartbeat and per-device queued/leased/uncertain totals. Previous implementation sent TWO distinct SELECTs. Return schema, device-specific counts, connected freshness threshold of 90s and backend are retained. No cache, no write and no reap on the signed status route.
The authenticated router heartbeat now executes a direct UPDATE for an already-enrolled device and falls back to INSERT ON CONFLICT only for first enrollment. Stored JSON payload and seen_at timestamp semantics preserved. Existing Go agent still sends every 60 seconds, with 90-second offline threshold unchanged. No changes to Windows binary, poller, Hostinger, OAuth, controller leases, idempotency, database schema or alternate Git routes.

## Acceptance evidence
1. Model-side executable JavaScript test of EXACT current source fragments fetched from GitHub (mcp.js SHA a22cf59949a2124b1185fc1d64a8a8bb1d450acb, router.js SHA b328b51523f618646f91f03c7ca3849e3d9144ae), instrumented query client: ESTABLISHED_HEARTBEAT_ONE_UPDATE PASS (1 operation); FIRST_HEARTBEAT_ENROLLMENT PASS (UPDATE miss and fallback INSERT); SIGNED_PRESENCE_SINGLE_SELECT PASS (1 statement, connected + counters); PRESENCE_CONNECTIVITY_90S PASS.
2. New single-SELECT signed status SQL executed read-only against production Neon project purple-flower-35918989/branch br-crimson-unit-b89nau08: current device heartbeat and queue counters returned; original heartbeat and count queries returned matching device identity and contemporaneous totals (active queue can change during sequential readings). Unknown-device SQL returned NULL heartbeat/seen_at and all counts zero. No production write tests or schema mutation.
3. All six Vercel source files passed syntax parsing or JSON parsing prior to deployment. Explicit source bytes were fetched from the exact GitHub branch commit d6204db9f0800e7a83275821bafc63a1065a4f1f and submitted in one Vercel create_deployment call. Vercel reports deployment dpl_H3k2Fuy3ee9A2px9AGcwQwVTusdF READY; both aliases present, Vercel source tree confirms src/api/mcp.js, src/api/router.js and other modules.
4. Signed Anthares Remote session_status returned connected=true, backend=vercel-neon, seen_at=2026-10-28T23:11:01.291Z with queue counters after new deployment. Neon independently read seen_at=2026-10-28T23:11:16.849Z at 23:11:22.866Z (heartbeat age ~6s), proving continued receipt and persistence. Vercel runtime counts show authenticated /v1/mcp/status and /v1/mcp/execute requests on new deployment.
5. Prior known-good reserve production deployment dpl_2FBscGWGbwXXCF7rCQ67DMDDieQw remains available for rollback.

## Accuracy / boundaries
The reduction is 2→1 SQL statement per signed presence request (50% on THAT route); normal heartbeat uses 1 UPDATE instead of 1 UPSERT. Do NOT interpret as 50% reduction of all Neon SQL or CU-hours; those are separately measured in fixed item12. The wake-only notifier, leases, and idem keys remain unchanged. Item6 event subscriber and item7 idle polling elimination remain open.
GitHub create_pull_request was explicitly blocked by security settings; no PR or GitHub Actions result is asserted for this item and no alternate route was attempted. Tests were source-level JS executed with query instrumentation plus read-only SQL executed on actual Neon, followed by successful signed production readback. The source remains committed on isolated feature/ara-item8-heartbeat-presence-20261028 branch, from which the exact deployed files were submitted.
