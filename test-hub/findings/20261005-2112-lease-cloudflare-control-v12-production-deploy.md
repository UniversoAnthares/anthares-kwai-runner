# Lease cloudflare-control: deploy validated v12 snapshot to production
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: production-deploy
COMMIT: pending
SUPERSEDES: none

LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-06T00:28:00Z

BASELINE_PROVEN: test-hub/findings/20261005-2020-control-plane-final-snapshot-proven.md; test-hub/findings/20261005-2022-cloudflare-wrangler-dryrun-proven.md; test-hub/findings/20261005-2016-cloudflare-local-oauth-deploy-path-proven.md; production read-only probe proved the current deployed Worker is stale and still exposes local fallback.
FAILED_AVOIDED: do not repeat the public-runner deployment path without CLOUDFLARE_API_TOKEN; do not use the failed private-runner path; use the already-authenticated Wrangler OAuth console solely for deployment. Runtime remains Cloudflare. Acceptance requires exact version and pc_fallback=false, so a green health endpoint alone is insufficient.
SUCCESS_SIGNAL: Wrangler production deploy completes, public `/health` returns `version=2026-10-05-no-pc-confirmation-v12` and `pc_fallback=false`, and read-only `/strategy`/self-test no longer exposes local/PC fallback.
FAILURE_SIGNAL: Wrangler deploy fails, health keeps old version, pc_fallback is not false, or any automatic strategy still returns local/PC.
TEST_VALIDITY: deploy source must be a fresh clone/current main after this lease is acquired; post-deploy verification must query the public Worker rather than local source.

## Objetivo
Promote the already statically validated and dry-run validated v12 controller snapshot so the new Kwai started/complete OIDC lifecycle can safely use production.
