# TikTok safe preflight round 2 lease
STATUS: RUNNING
AREA: tiktok-safe-preflight-r2
DATE: 2026-10-06
OWNER: CHAT 3

BASELINE_PROVEN: public control health succeeded; Render session-status succeeded with bootstrapped=true, identity_verified=true, ready_for_tiktok=true. Queue-health using the new workflow_ref returned 401, proving Cloudflare allowlisting is workflow_ref-specific.
FAILED_AVOIDED: do not retry the same queue-health identity. Round 2 varies auth/contract surfaces and performs no started/publish.
SUCCESS_SIGNAL: five independent probes characterize allowed/denied OIDC surfaces and fail-closed behavior without queue mutation.
FAILURE_SIGNAL: unexpected acceptance of invalid auth or loss of known-good Render identity.
TEST_VALIDITY: no publication endpoint, no publication_started, no TikTok mutation.
