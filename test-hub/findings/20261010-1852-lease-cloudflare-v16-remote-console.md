# Lease: restore deployed Cloudflare queue-fencing-v16 using authorized remote console
STATUS: RUNNING
AREA: cloudflare-control
DATE: 2026-10-10
OWNER: chatgpt-qa-handoff-1852Z
LEASE_UNTIL: 2026-10-10T19:17:03Z
HEAD_BASELINE: 4bad2ebb7fd6e821474bd3d7f576479419d703a0
RESOURCES: cloudflare-worker/src/index.js; cloudflare-worker/wrangler.toml; remote admin console only
BASELINE_PROVEN: /health at 18:49:16Z returns no-pc-confirmation-v12 while repository source/workflow expects queue-fencing-v16. Kwai PR #23 merged; run 38077415448 preflight passed and publish skipped on stale control.
FAILED_AVOIDED: GitHub deploy action has no CLOUDFLARE_API_TOKEN, do not rerun that failed path; use already authorized Wrangler OAuth if available, without showing or copying tokens. No Android, no PC publisher, no queue mutation.
SUCCESS_SIGNAL: Wrangler deploy exact repository main SHA and independent public /health confirms version queue-fencing-v16, persistent_state=true, queue_bound=true, pc_fallback=false.
FAILURE_SIGNAL: OAuth unavailable, deployment error, or postdeploy health not v16.
TEST_VALIDITY: no claims about real video publication or session identity; validate source and account before deployment. Do not touch browser tabs or show windows.
SUPERSEDES: none
