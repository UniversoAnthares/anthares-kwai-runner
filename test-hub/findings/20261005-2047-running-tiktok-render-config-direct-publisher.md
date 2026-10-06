# RUNNING — TikTok Render direct-publisher readiness contract
STATUS: RUNNING
AREA: tiktok-render-config
DATE: 2026-10-05
OWNER: CHAT 5

PROVEN_BASELINE:
- Live Render session/account identity is PRODUCTION PROVEN by run 37395199814.
- `render-tiktok-worker/service.py` direct endpoints `/publish` and `/publish-url` consume media directly and authenticate with Render OIDC.
- `tiktok_web_publish_local.py`, the subprocess invoked by both direct endpoints, does not consume `ANTHARES_VIDEO_ENDPOINT` or `ANTHARES_VIDEO_SECRET`.
- `validate_secrets.py` identifies those variables as credentials for the legacy Anthares Video API bridge.

HYPOTHESIS:
`/config-status` should expose direct-publisher readiness separately from legacy video-bridge configuration. Its top-level `ok` should require the current direct TikTok prerequisites (expected username, expected user ID, bootstrapped session, verified identity), while retaining legacy endpoint/secret booleans as observability fields.

SUCCESS_SIGNAL:
- Static regression proves missing legacy secret does not make direct publisher readiness false when session+identity+expected account fields are present.
- Missing expected account fields, session, or identity remains fail-closed.
- Legacy bridge status remains explicit and false when its secret is absent.
- Render deploy reaches live revision and production config-status reports direct publisher ready.

SAFETY:
No publication is part of this experiment. No Cloudflare queue/control-plane code is modified. No credential values are created, exposed, or changed.
