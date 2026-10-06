# RUNNING — TikTok Render rehydrate via approved Cloudflare workflow_ref
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-05
OWNER: CHAT 5

PROVEN_BASELINE: `.github/workflows/tiktok-central-session-read.yml` is accepted by Cloudflare v12 and returned HTTP 200, available=true, 21 cookies. The alternate workflow_ref returned HTTP 401 before Render mutation.
HYPOTHESIS: extending the already-approved `tiktok-central-session-read.yml` preserves the authorized OIDC principal and allows one safe chain: central GET -> Render `/bootstrap-session` -> `/session-status` -> `/session-test` with identity_verified=true -> refreshed central POST -> Render `/config-status`.
SUCCESS_SIGNAL: CENTRAL_SESSION_AVAILABLE plus safe milestones for Render bootstrap, bootstrapped status, identity_verified=true, central persist, config ok, and `TIKTOK_RENDER_REHYDRATE=PRODUCTION_PROVEN`.
FAILURE_SIGNAL: any 401/403, bootstrap failure, identity mismatch, missing refreshed state, central persist failure, or config incomplete.
SAFETY: keep state only in the ephemeral runner file; never print cookies/tokens; never call `/publish-url`; do not mutate Cloudflare code or queue logic.
