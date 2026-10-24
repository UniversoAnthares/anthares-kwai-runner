# Kilo OAuth client enrollment
STATUS: RUNNING
AREA: ara-mcp-kilo-oauth
LEASE_OWNER: codex-kilo-auth-20261024
EXPIRES_UTC: 2026-10-24T13:37:12.505320+00:00
BASELINE_PROVEN: main a7633da; GitHub/GitLab index blob 2e215ef224f8d96ceb7d4c5dfbf1e84782f8e8a8 equal; ARA connector operational; Kilo official metadata verified.
FAILED_AVOIDED: Kilo client and callback absent from enrollment policy; trailing slash resource differs. Do not weaken generic client/redirect checks, replace ChatGPT pin, keys, owner identity or Claude scopes.
SUCCESS_SIGNAL: exact Kilo client/callback, PKCE/owner/scope/replay regressions pass, official reviewed deployment and real Kilo auth/tools succeed.
FAILURE_SIGNAL: untrusted loopback/callback accepted, pin changed, unauthorized scopes, existing clients regress or active deploy conflict.
TEST_VALIDITY: local tests prove policy only; deployed Kilo OAuth/tool call remains independent acceptance.
SCOPE: cloudflare-ara-mcp client enrollment policy and tests only. No CORTES, publications or credentials.
