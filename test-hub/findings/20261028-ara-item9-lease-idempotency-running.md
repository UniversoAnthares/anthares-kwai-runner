# ARA Event-Driven — item 9 exclusivity and idempotency during migration
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / queue
DATE: 2026-10-28
RUN: none
JOB: ARA item 9 user-directed acceptance
COMMIT: a5fa5bdc0fbc3a3af14a75abbe262037bd9cef54
SUPERSEDES: none
LEASE: 2026-10-28T22:47:00Z through 2026-10-28T23:17:00Z; independent test layer only.

## BASELINE_PROVEN
Production reserve deployment dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb READY, signed Cloudflare MCP targets production reserve aliases. Wake-only Hostinger item 5 PROVEN. Neon schema: UNIQUE(device_id,idempotency_key) WHERE NOT NULL, primary key(id), status CHECK, attempts, lease_until. Read-only 24h evidence: 3498 jobs all with idempotency keys; zero duplicate (device,key), 2 safe system_info retries, no completed jobs executed more than once, device connected. Gateway Cloudflare worker passes a stable cfmcp-<UUID> idempotency_key to both reserve aliases; source api/mcp.js currently discards this input and generates a new random key. This is a migration duplicate risk.

## FAILED_AVOIDED
Avoid mutating Neon production, creating live jobs or altering Windows processes. Never repeat a command for verification after timeout. No schema, publisher, OAuth, agent, GitLab or Cloudflare worker changes. GitHub and GitLab source hashes differ; GitLab duo-main does not carry reserve/api/mcp.js. Do not overwrite concurrent PR #1817, create isolated branch and PR.

## SUCCESS_SIGNAL
(1) MCP signed execute passes gateway's idempotency key to atomic Neon INSERT ON CONFLICT DO NOTHING, duplicate lookup returns original ID and rejects conflicting payload.
(2) Only newly inserted queued job triggers Hostinger wake; duplicate key does not emit wake.
(3) Both control routes preserve atomic single-row claim via FOR UPDATE SKIP LOCKED and correct handling of uncertain/non-retryable jobs.
(4) Unit/SQL concurrency tests prove one row, one acquisition/attempt, no second wake, mismatch fail-closed and late result non-reexecution.
(5) Production Vercel correct deployed SHA ready, alias readback, original Neon history remains free of dupes; rollback candidate preserved.
(6) No direct production database mutation for tests.

## FAILURE_SIGNAL
Two distinct jobs for same (device,idempotency_key); repeated wake on existing id; double lease claim; accidental requeue of unsafe shell after lease expiration; deploy health regression, stale branch head or another active conflicting lease.

## TEST_VALIDITY
CI must report explicit per-invariant labels and post-change application readback. A successful CI alone does not establish rollout. All tests run in ephemeral Postgres or offline stubs, no new Windows command or production Neon rows.
