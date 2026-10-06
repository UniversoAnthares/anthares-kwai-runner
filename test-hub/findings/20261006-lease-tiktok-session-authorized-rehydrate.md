# Lease tiktok-session — authorized central read/rehydrate probe
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
EXPIRES: 2026-10-06T04:25:00Z
BASELINE_PROVEN: Render session currently reports bootstrapped=false, identity_verified=false, ready_for_tiktok=false; previous direct diagnostic OIDC received HTTP 401 because its workflow identity was not deployed in the Cloudflare allowlist. The already-deployed allowlisted workflow is tiktok-central-session-read.yml.
FAILED_AVOIDED: do not use tiktok-reconcile-v2.yml identity; do not publish; do not create a second canary; do not repeat the old unauthorized diagnostic route.
SUCCESS_SIGNAL: tiktok-central-session-read.yml obtains HTTP 200 central session metadata, rehydrates Render, session-test verifies identity, persists refreshed state, and reaches TIKTOK_RENDER_DIRECT_READY=PRODUCTION_PROVEN.
FAILURE_SIGNAL: allowlisted workflow still receives 401/403, central session is absent, Render rehydration fails, or identity verification fails.
TEST_VALIDITY: workflow obtains GitHub OIDC itself, validates central cookie/origin structure, reports each HTTP status, and requires identity_verified=true before success.