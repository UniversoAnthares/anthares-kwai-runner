# ARA item 5 — Hostinger notification emitter deployed; broker receipt pending
STATUS: PARTIAL
AREA: anthares-remote / neon-idle-optimization / vercel-ara-primary
DATE: 2026-10-28
RUN: Vercel deployment dpl_k7VUu3p222MnC4rNeLAZp6q84zFf (production READY)
JOB: Neon ara_reserve_jobs a8d42577f346772769b58bf87a335639 (file_stat done)
COMMIT: e8a9609ce6e6b2948082ba02a490b87ee0641ced
SUPERSEDES: 20261028-ara-item5-hostinger-vercel-lease.md

## Result
Hostinger wake notifier and seven tests installed in isolated branch feature/ara-item5-hostinger-vercel-20261028, PR #1815. Code emits after Neon INSERT/UPSERT only. Protected Vercel Production secret ARA_WAKE_NOTIFY_SECRET is present. ARA_WAKE_NOTIFY_ENABLED=1 was read back independently. Final production deployment dpl_k7VUu3p222MnC4rNeLAZp6q84zFf is READY at exact SHA e8a9609. Runtime log emits ara_wake_broker_recorded plus sequence when a broker 202 receipt is parsed; failures log ara_wake_broker_unconfirmed and never roll back the job. No changes to Neon schema, leases, OAuth, C8 agent, Git queues or public publishers.

## Acceptance
Offline Node contract tests 7/7 PASS. Native ARA file_stat returned done for D:\\AntharsWork\\governance\\INDICE.md; Neon readback shows status done for job a8d42577f346772769b58bf87a335639 (created 2026-10-28T21:41:31Z). Runtime logs in Vercel with query ara_wake did not return a positive sequence receipt during this window. This is not yet proof that Hostinger recorded the event or that the emitter was invoked for this particular MCP route; investigate exact calling deployment or check protected Hostinger state. Do not mark item 5 fully PROVEN without the broker receipt.

## Concurrency/rollback
Deployment before item5: dpl_GnZzoFiPi5BKGCZGayLJD7kU3oet SHA e32a2bba7ad086d5e0eccd7b7b8d6a54b9e20fda. Rollback immediately by production flag 0 + new deployment or Vercel rollback if evidence of regression. Concurrent PR #1808 (Cloudflare wake + C8 subscriber) remains separate. No further live smoke commands required until receipt route is identified.
