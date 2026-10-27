# Quota cancellation — Anthares CI (v1)

Effective rule: `CANCELAR_IMEDIATAMENTE_POR_COTA_V1`.

When an owned job or execution stops because of a **confirmed** provider quota, usage or credit limit, the controller must immediately request cancellation of that exact remote job, even if an alternative provider is available. The original execution must not remain waiting for quota reset.

Before a fallback: verify remote terminal status (canceled/failed/terminated/expired) and revoke the original execution lease. For any side-effectful task (publishing, purchases, writes), obtain `NOT_APPLIED` reconciliation. Only then enqueue a **new** idempotent attempt with an eligible standby on a demonstrably independent quota scope.

If cancellation or submission is uncertain: fail closed, retain the task in the safe queue and reconcile; never retry blindly, dispatch in parallel, charge a paid plan, weaken authentication or treat a credential denial as quota.

Code: `tools/ci_quota_cancel_first.py`; tests: `tests/test_ci_quota_cancel_first.py`. The SQLite implementation is **single-host only** and its callbacks have no credentials. Production multi-cloud execution needs a shared transactional lease/fencing ledger and provider-specific cancel, status and enqueue callbacks. The router declares this contract but automatic cancellation is **not yet integrated** into every provider. Never mark a provider operational without real cancellation evidence.

Provider requirements: GitLab pipeline cancellation and status APIs; GitHub Actions run cancellation and status APIs; AppVeyor and Bitrise own provider cancellation APIs; Cloudflare Workers Builds and other platform-specific jobs need separate adapters. No exception for Northflank jobs, browser tasks, social publishers, SMTP or AI: each must either support confirmed cancellation and safe independent failover or stop fail-closed with `CANCEL_UNCONFIRMED` or `CANCELLED_NO_INDEPENDENT_RESERVE`.

Existing CI priority order is unchanged. AppVeyor remains penultimate and GitLab CI last; blocked providers cannot be promoted without a fresh successful run and quota proof. This document is an implementation requirement, **not** proof every platform's adapter is live.
