# ARA item 8 — optimize heartbeat writes and presence SQL without delaying detection
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / queue-read-presence
DATE: 2026-10-28
RUN: pending
JOB: user-directed fixed item 8
COMMIT: 675f4bfccbbfa2ef02f6a4e4d769b0da001ee1d2
SUPERSEDES: none
LEASE: 2026-10-28T23:07:00Z through 2026-10-28T23:37:00Z; isolated read-presence layer; not the event subscriber or poller.

## BASELINE_PROVEN
Signed gateway Cloudflare /v1/mcp/status reaches Vercel reserve API mcp.js; current status() performs two serial SQL SELECT queries per request (heartbeat row and jobs grouped counts). Windows Go heartbeat interval 60s, status live threshold 90s; changing cadence or timeout prematurely could cause false disconnection. Vercel reserve router.js /v1/device/heartbeat currently performs INSERT ON CONFLICT DO UPDATE on every successful heartbeat, even for an existing device. Neon row at 2026-10-28T23:07:09Z seen_at ~13s old, heartbeat_time ~23s old. Item9 lease+idempotency protection is PROVEN (GitHub CI run 40783018867, production dpl_2FBscGWGbwXXCF7rCQ67DMDDieQw READY). Current branch derives from exact post-item9 HEAD 675f4bfccbbfa2ef02f6a4e4d769b0da001ee1d2.

## FAILED_AVOIDED
No polling changes (item7); no Windows agent update (item6), no wake transport change (item5), no lease or idempotency change (item9), no Neon schema modifications or live mutation tests. Do not extend heartbeat TTL to save negligible SQL but degrade 90s detection. Do not merge/replace other agent's branches.

## SUCCESS_SIGNAL
Canonical signed status performs ONE parameterized SQL SELECT while returning exactly the previous heartbeat/seen_at/connected (<=90s)/queued/leased/uncertain/backend semantics for present, absent and stale devices, and correct counts at any state. Authenticated /v1/device/heartbeat performs ONE UPDATE on normal existing device, INSERT ON CONFLICT only for unregistered device, preserving full JSON and seen_at semantics. PostgreSQL 16 isolated integration tests prove these facts; production Vercel exact source deployment READY, both aliases mapped, real gateway status reports connected without increasing Neon table anomalies, and approved rollback version remains READY. No new queues or Windows commands created.

## FAILURE_SIGNAL
Wrong counts/device mapping, dropped heartbeat JSON/time field, stale connected true, increased normal-case query count, authentication/lease regression, failed CI or READY, stale deployment head/alias collision.

## TEST_VALIDITY
Only CI ephemeral Postgres creates/drops test tables. No new queries against production aside from read-only sampling; Vercel production smoke via signed status only. Green build without explicit success labels insufficient for PROVEN.
