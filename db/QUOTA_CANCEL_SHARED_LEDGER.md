# Anthares shared quota-cancellation fencing ledger

Live deployment on 2026-10-27: project `anthares-ara-ha`, main branch
`br-crimson-unit-b89nau08`, database `neondb`, schema `anthares_quota`.
QA validation on branch `br-quiet-unit-b8w1tqmf`.

Migration: `db/quota_cancel_shared_fencing.sql`. Uses isolated schema with revoked
PUBLIC privileges, two empty tables (`attempts`, `provider_health`), and
three SECURITY INVOKER functions. No modification of existing publishing tables.

PostgreSQL cancellation protocol:
1. Record the owned job in `attempts` with `RUNNING`, nonzero fence and
   authenticated `lease_owner`.
2. When a provider confirms exhausted quota, call `begin_cancellation` with
   exact attempt id, expected fence and lease owner; it advances the fence and
   enters `CANCEL_REQUESTED`.
3. Independently invoke the exact provider's *real* cancel endpoint and poll
   until terminal. No fallback while cancellation is unconfirmed.
4. After externally confirmed terminal status and `NOT_APPLIED` proof, call
   `confirm_cancellation` with the new fence. The database refuses stale
   fence and nonterminal status.
5. Only then call `reserve_successor` with a provider whose independent
   quota status was verified within 30 minutes. The partial unique index
   prevents two simultaneously active attempts for the same task.
6. No eligible reserve => keep a terminated, safe task with no active job.
   Never purchase capacity, blindly retry, restart the original attempt, or
   bypass authorization.

The 2026-10-27 isolated QA DO test verified stale-fence rejection,
nonterminal rejection, same-quota rejection, one independent successor and
duplicate-succcessor rejection; QA rows were deleted.

IMPORTANT: this is a **deployed shared durable data-plane** but **not yet an
operational multi-provider event-plane**. The deployed SQL does not itself
cancel GitHub/GitLab/AppVeyor/Bitrise/Cloudflare/Northflank jobs. Controllers
must be wired to quota signals, APIs, signed status receipts, service-specific
least-privilege credentials and epoch checks for every side-effectful writer.
A provider must remain ineligible until a real end-to-end cancellation/failover
drill passes. Do not grant database access to PUBLIC or use DB-owner password
as a publisher credential.
