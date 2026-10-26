# CF-03 — Cloudflare Queues/DLQ isolated QA fixture

This directory preserves the exact Worker source and Wrangler configuration used for the **2026-10-25** Cloudflare real-network acceptance test. It is **not a production publisher**, and must never be merged into a social network publisher path or deployed under the production controller name.

## Ownership and scope
- Worker: `anthares-cf03-qa-r0725`; queues: `cf03-qa-main-r0725`, `cf03-qa-dlq-r0725`.
- Single SQLite-backed Durable Object namespace `Cf03Ledger` stores synthetic message attempts/effects/DLQ receipts in a separate SQL ledger with unique IDs.
- No TikTok, Kwai, YouTube, Instagram or other social API, external HTTP fetch, production KV/DO, cloud database, route, cron, or credentials. All external endpoints other than GET health/status return 404/401.
- The POST seed endpoint requires the ephemeral Worker secret `CF03_RUN_KEY` and a single durable claim. The test token was **deleted after the successful test**; the Worker cannot accept another seed without an explicitly authorized new secret and new fixture contract.
- Queue consumer handles only the three fixed synthetic test IDs. Retry-once delivers twice but creates one unique effect. Always-fail delivers twice and reaches the QA DLQ. Runtime source exports no publication capability.
- Free-plan Queues allowance is 10,000 operations/day and 24-hour retention according to Cloudflare documentation as of 2026-10-25. No account plan or billing settings were changed. Account billing proof was not inspected.

## Real acceptance evidence
- Main queue ID: `17cb65c82df14ba5b94eea0aa30fedb0`; DLQ ID: `498d0e0165ca4512bc50b8d9b11f3185`.
- Cloudflare Wrangler 4.149.0: `node --check` PASS; `wrangler deploy --dry-run` PASS; live Worker deploy PASS, two consumer registrations and one producer binding.
- Live HTTP /health PASS, no external destinations and `publication_allowed=false`. Unauthenticated seed HTTP 401 before and after removing the temporary secret.
- Three synthetic messages accepted (HTTP 202). Durable object /status: normal attempts=1, retry_once attempts=2, always_fail attempts=2; **effects ledger contains exactly normal and retry_once**; **DLQ ledger contains exactly always_fail**; seeds=1.
- Production `anthares-control` health=200, v18, queue_bound=true before and after; no publication sent.
- Final Worker secret-list readback confirms `CF03_RUN_KEY` absent; no scheduled workload.
- Test Hub finding: `test-hub/findings/20261025-cf03-queues-dlq-proven.md` (same review branch). This is an isolated QA acceptance only, not a production cutover or IAM/network segregation proof.

## Safe reuse
Do not replay these IDs, resend already claimed seed, attach production publisher code, or alter the existing queues without a new Test Hub lease and explicit owner assignment. For a new run, create new names/job IDs and plan cleanup/retention and billing checks. Keep the two historical queue IDs as immutable evidence. Preserving the fixture in Git does not authorize another deployment.
