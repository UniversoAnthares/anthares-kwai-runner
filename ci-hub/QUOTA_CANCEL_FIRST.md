# Quota cancellation — Anthares CI (v1)

Effective rule: `CANCELAR_IMEDIATAMENTE_POR_COTA_V1`.

When an owned job or execution stops because of a **confirmed** provider quota, usage or credit limit, the controller must immediately request cancellation of that exact remote job, even if an alternative provider is available. The original execution must not remain waiting for quota reset.

Before a fallback: verify remote terminal status (canceled/failed/terminated/expired) and revoke the original execution lease. For any side-effectful task (publishing, purchases, writes), obtain `NOT_APPLIED` reconciliation. Only then enqueue a **new** idempotent attempt with an eligible standby on a demonstrably independent quota scope.

If cancellation or submission is uncertain: fail closed, retain the task in the safe queue and reconcile; never retry blindly, dispatch in parallel, charge a paid plan, weaken authentication or treat a credential denial as quota.

Code: `tools/ci_quota_cancel_first.py`; tests: `tests/test_ci_quota_cancel_first.py`. The SQLite implementation is **single-host only** and its callbacks have no credentials. Production multi-cloud execution needs a shared transactional lease/fencing ledger and provider-specific cancel, status and enqueue callbacks. The router declares this contract but automatic cancellation is **not yet integrated** into every provider. Never mark a provider operational without real cancellation evidence.

Provider requirements: GitLab pipeline cancellation and status APIs; GitHub Actions run cancellation and status APIs; AppVeyor and Bitrise own provider cancellation APIs; Cloudflare Workers Builds and other platform-specific jobs need separate adapters. No exception for Northflank jobs, browser tasks, social publishers, SMTP or AI: each must either support confirmed cancellation and safe independent failover or stop fail-closed with `CANCEL_UNCONFIRMED` or `CANCELLED_NO_INDEPENDENT_RESERVE`.

Existing CI priority order is unchanged. AppVeyor remains penultimate and GitLab CI last; blocked providers cannot be promoted without a fresh successful run and quota proof. This document is an implementation requirement, **not** proof every platform's adapter is live.

## Shared transactional ledger (2026-10-27)

An **opt-in**, cross-host PostgreSQL ledger implementation now exists in `tools/ci_quota_neon_ledger.py`; its additive schema is versioned in `db/migrations/20261027_ci_quota_fenced_ledger.sql`, with unit tests in `tests/test_ci_quota_neon_ledger.py`. It provides atomic first claim, per-owner token, generation-based compare-and-swap, bounded lease and fail-closed rejection of stale updates. An expired attempt cannot be reclaimed automatically; independent remote-status and side-effect reconciliation remain mandatory.

QA evidence: GitHub Actions run [40504599465](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504599465) passed 6 tests and printed `CI_QUOTA_LEDGER_QA=PASS`. A separate rollback-only Neon QA transaction validated real PostgreSQL constraints and fencing semantics, then verified the table was absent after rollback (see `test-hub/findings/20261027-ci-quota-postgres-real-qa-rollback-proven-chatgpt.md`).

**Current production status (2026-10-27):** This schema IS deployed on Neon main (project purple-flower-35918989), under the SQL-created restricted `anthares_ci_quota_limited` role. Vercel `anthares-ci-quota-controller` is live with OIDC and `ledger=READY`. GitLab quota handoff to independent GitHub CI is operational for one observed real incident: pipeline 2994547840 -> GitHub run 40510154187 SUCCESS, Neon `FALLBACK_CONFIRMED`.

**External providers:** PR #1557 installed a separate 15-minute GitHub Actions watcher for AppVeyor/Bitrise with an exact account/project/commit check, structured quota evidence, cross-host Neon exclusive claim, provider cancellation/status API, and fail-closed reconciliation. Deployment READY; however, provider API credentials and app/project variables remain unconfirmed. No real AppVeyor/Bitrise quota incident has been observed or canceled. The existing GitHub Actions own-run callback is also not yet universally wired. A green deployment alone is not evidence of remote cancellation; see `test-hub/findings/20261027-appveyor-bitrise-quota-watcher-implemented-auth-pending.md`.
