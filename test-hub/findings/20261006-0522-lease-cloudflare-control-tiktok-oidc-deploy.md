# Lease: Cloudflare control TikTok OIDC deploy
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-06
LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-06T05:50:00Z
BASELINE_PROVEN: deployed queue/control semantics v16 are PROVEN; repository source already contains the TikTok workflow OIDC allowlist fix.
FAILED_AVOIDED: do not retry TikTok publish against the currently deployed control while it returns HTTP 401; deploy the reviewed source first. Do not change queue semantics.
SUCCESS_SIGNAL: fresh-clone Wrangler OAuth deploy succeeds; public /health remains healthy; TikTok workflow OIDC reaches queue endpoint without HTTP 401.
FAILURE_SIGNAL: deploy fails, health regresses, or authorization remains HTTP 401 after deployment.
TEST_VALIDITY: deploy exact current main snapshot from a fresh clone; verify public health before any TikTok retry.

## Objective
Close the current TikTok authorization blocker without changing publisher or queue semantics.
