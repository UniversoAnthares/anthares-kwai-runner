# Recover ARA control, dedicated browser, and independent WordPress mirror
STATUS: RUNNING
AREA: ara-control, browser-session, wordpress-mirror
DATE: 2026-10-18
LEASE_OWNER: codex-01a14ef0
LEASE_EXPIRES_UTC: 2026-10-18T12:53:00Z
BASELINE_PROVEN: GitHub runner c82cb882; WordPress GitHub 4e24f527 and GitLab 1154ec97. Canonical SYSTEM supervisor targets Vercel/Neon with two private issue queues. On-disk device token matches published hash and auth-check succeeds, but running agent reports 401 and backend heartbeat is stale. MCP capabilities returns 401. Dedicated CDP 9223 absent. WordPress QA Vercel build fails orchestrator QA.
FAILED_AVOIDED: do not rotate already-matching device credentials blindly; do not use old D-drive supervisor snapshots as canonical; no Cloudflare OAuth reconnect, no paid service, no forbidden providers.
SCOPE: canonical Remote configuration and legitimate MCP compatibility; dedicated isolated Anthares Browser; WordPress non-destructive mirror with remote scheduler independent of CI minutes. No anthares-clipper changes, CORTES changes, Android executors/queues, reboot, shutdown, or user logoff. Independent from consumer-recovery lease in kwai-publish/android-runtime.
SUCCESS_SIGNAL: real harmless Remote job acknowledged once, unauthorized request rejected; authenticated dedicated browser survives restart; automatic remote GitHub-to-GitLab mirror preserves both histories/content and passes idempotence/failure-recovery tests.
FAILURE_SIGNAL: authorization or fencing regression, competing SYSTEM executor, unreconciled divergence, missing scheduled-run evidence.
TEST_VALIDITY: fresh provider HEAD/blob reads, peer comparison and optimistic concurrency before each write; distinguish manual invocation from actual scheduled invocation. Current workflows/pipelines inspected; no active run in this causal chain.
SUPERSEDES: none
