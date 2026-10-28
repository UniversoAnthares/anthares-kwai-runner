# ARA Event-Driven — item 9: leases and idempotency during notification migration
STATUS: PROVEN
AREA: anthares-remote / neon-idle-optimization / queue
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40783018867
JOB: GitHub Actions PostgreSQL integration 123149175581
COMMIT: ed12002eff4c27aa9cc02552b90fbe0b74477b9e
SUPERSEDES: 20261028-ara-item9-lease-idempotency-running.md

## Verified baseline / original risk
Cloudflare signed MCP gateway sends a stable `cfmcp-<uuid>` key in the POST body to either canonical or standby reserve alias; existing reserve api/mcp.js previously discarded that key and generated a distinct random one per request, allowing duplicate jobs on fallback.
Production Neon project purple-flower-35918989 branch br-crimson-unit-b89nau08 schema contains UNIQUE(device_id,idempotency_key) partial index and primary key(id). No production database mutation used in tests.

## Implemented
In independent PR #1823, based on existing item5 implementation PR #1817: reserve signed MCP `create()` now accepts the supplied idempotency_key, inserts with atomic PostgreSQL `ON CONFLICT(device_id,idempotency_key) ... DO NOTHING RETURNING id`, and on conflict returns the existing job ID only after payload type/args/timeout equivalence. Mismatch fails closed with HTTP 409. Hostinger wake is triggered only when insertion creates the job; replay never duplicates wake. Existing signed Ed25519 auth, OAuth replay store, source router's SKIP LOCKED lease, reconciliation and result handling unchanged. No changes to Cloudflare gateway, Neon schema, Windows agent, publishers or standby alias.

## Decisive integration evidence
- GitHub Actions run 40783018867, job 123149175581: completed SUCCESS on PostgreSQL 16 isolated service, with real SQL executed (not production). Explicit log signals: ARA_ITEM9_DEDUPE_CONCURRENT_PASS; ARA_ITEM9_CONFLICT_FAIL_CLOSED_PASS; ARA_ITEM9_SINGLE_LEASE_AND_TERMINAL_IMMUTABLE_PASS; ARA_ITEM9_UNCERTAIN_MUTATING_NEVER_RETRY_PASS.
- Seven parallel requests with one idempotency key returned a single job ID and triggered a single wake; retries with same JSONB payload reordered returned same job; changed args/type/timeout failed closed.
- Two independent workers using real PostgreSQL SELECT FOR UPDATE SKIP LOCKED could not acquire the same queued job. A leased job was not claimed again; successful completion remained immutable to a conflicting second result.
- Expired mutating `shell` lease became `uncertain` and did not auto-requeue; explicitly safe `system_info` could be retried.
- Existing wake-only CI workflow also SUCCESS on same patch SHA.
- Vercel project prj_i5ylgY1BgnrPZzSoBZ5UMOtJX77P production deployment dpl_2FBscGWGbwXXCF7rCQ67DMDDieQw READY with canonical and standby aliases independently read back. Built from the six exact review-branch source files, including modified api/mcp.js.
- Signed Anthares Remote live status: connected=true, backend=vercel-neon. Production Neon read-only: duplicate_keys=0; last 10m 125 jobs, repeated_claims=0, multi_attempt_done=0, uncertain=0. During prior 24h 3498 jobs and zero duplicate keys, 2 safe system_info retries (status failed), no multiattempt completion.
- Rollback candidate dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb remains ready. Change confined to enqueue idempotency; lease and authentication code preserved.

## Scope and current caveat
The item9 property — queue deduplication, single lease acquisition and fail-closed unsafe expiry during migration — is PROVEN. This is not proof that the Windows event subscriber has replaced polling (item6), that fallback is implemented (item10), or that idle Neon SQL/CU hours are reduced (items7/12). After this deployment, Vercel runtime logs have occasional Hostinger wake HTTP 403/timeout errors; the broker transport is fail-open and the authoritative Neon jobs proceed independently. Monitor/reconcile under appropriate later items; do not confuse notification delivery with queue deduplication or claim all notifications always succeeded.

## Coordination
Keep PR #1823 code in the final reserve source merge; its base PR #1817 is older and lacks gateway-idempotency preservation. Do not deploy the older mcp.js verbatim over the newer READY version. Avoid parallel gateway publishers and any resend of uncertain mutating job; no production changes are needed for item9 after this evidence.
