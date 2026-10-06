# Lease — TikTok Render control authorization repair
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
LEASE_EXPIRES: 2026-10-06T14:05:00Z
BASELINE_PROVEN: Render service is live; /health and /config-status are 200; local /session-status reports its internal control-plane request as HTTP 403. TikTok env30 exhausted browser-environment permutations.
FAILED_AVOIDED: no environment/UA/viewport matrix, no publish, no cookie scraping, no duplicate irreversible canary.
SUCCESS_SIGNAL: Render -> control-plane read-only session request is authorized and /session-status can evaluate stored state; then authenticated /upload access is tested read-only.
FAILURE_SIGNAL: authorization remains 401/403, stored state is rejected, or legitimate owner reauthentication is required.
TEST_VALIDITY: no credentials/cookie values printed; read-only until authenticated upload access is positively proven.
