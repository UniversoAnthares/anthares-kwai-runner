# RUNNING — TikTok central session read after production Cloudflare v12
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-05
OWNER: CHAT 5

BASELINE_PROVEN: test-hub/findings/20261005-2117-cloudflare-v12-production-proven.md
FAILED_AVOIDED: do not repeat the pre-v12 central GET/env-seed probes that returned HTTP 403 / bootstrapped=false. This experiment is valid only because production Cloudflare changed to v12 with the GitHub OIDC allowlist deployed.
HYPOTHESIS: the existing read-only workflow `.github/workflows/tiktok-central-session-read.yml` is now authorized by production v12 and can distinguish CENTRAL_SESSION_AVAILABLE from CENTRAL_SESSION_ABSENT without publishing.
SUCCESS_SIGNAL: workflow reaches HTTP 200 + available=true + state cookies list and emits CENTRAL_SESSION_AVAILABLE.
ALTERNATE_VALID_RESULT: HTTP 404 + available=false emits CENTRAL_SESSION_ABSENT, proving auth is fixed while stored session is absent.
FAILURE_SIGNAL: HTTP 401/403 after v12 means the OIDC/session-read authorization path remains incorrect and needs a new causal fix.
SAFETY: read-only; no /publish call; no TikTok mutation; no Cloudflare deployment; does not interfere with the active Cloudflare v13 counter-reset deploy lease.
