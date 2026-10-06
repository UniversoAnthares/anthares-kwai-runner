# Lease cloudflare-control — deploy OIDC allowlist fix
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-06
LEASE_AREA: cloudflare-control
EXPIRES: 2026-10-06T04:25:00-04:00
BASELINE_PROVEN: deployed v16 control plane; repository source contains tiktok-reconcile-v2.yml in verifyGithubOidc allowlist.
FAILED_AVOIDED: do not retry the same TikTok reconcile while deployed control rejects it with HTTP 401; do not modify queue semantics.
SUCCESS_SIGNAL: WRANGLER_DEPLOY_OK=1 and CONTROL_HEALTH_OK=1, followed by tiktok-reconcile-v2 receiving non-401 authorization.
FAILURE_SIGNAL: deploy workflow fails or public health remains on an older version / reconcile authorization remains rejected after deployment.
TEST_VALIDITY: workflow validates exact repository snapshot before deploy and verifies public health after deploy.

## Objective
Deploy the already-reviewed Cloudflare control source containing the tiktok-reconcile-v2 OIDC allowlist entry.