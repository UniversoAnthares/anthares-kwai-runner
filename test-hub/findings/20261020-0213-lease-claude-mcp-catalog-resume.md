# Resume Claude MCP catalog and preserve canonical owner OAuth
STATUS: RUNNING
AREA: claude-mcp-tool-discovery
LEASE_OWNER: ChatGPT/mcp-catalog-resume
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/refresh-mcp-tool-catalog-20261020
START_UTC: 2026-10-20T02:11:13.141Z
EXPIRES_UTC: 2026-10-20T02:51:13.141Z
BASE_BRANCH_HEAD: fac5a39fc22dbd24fcd1bd213ebf7d45d75b9e03
BASE_MAIN_HEAD: 0490f609a0f4ee6f57bc00be3e0eb2d54ba2482d
BASELINE_PROVEN: Production ChatGPT→Anthares shared task→GitHub Actions→Claude Code 39356635285 completed success, Cloudflare deploy 39355914581 success; direct Claude Free owner result 39352658418 ready true. PR #218 earlier CI 39349007904 passed.
FAILED_AVOIDED: Earlier merge failure 405 was caused by ruleset "proteger-main" containing "update" restriction. Read of ruleset on 2026-10-20 now shows only non_fast_forward, deletion, pull_request; keep these protections. Never force-update main or replace GitHub owner OAuth with legacy email OTP. Do not alter already proven Claude/Work bridge.
SUCCESS_SIGNAL: PR #218 approved CI, merge via normal GitHub PR API succeeds; new reviewed Cloudflare deploy run succeeds, /health displays mcp_server_version=1.1.0 and exact published delegation tool names; anonymous MCP 401; Work issue #230 remains accessible.
FAILURE_SIGNAL: stale HEAD/peer mismatch, declined protected-merge rule, CI failure or deployment degrades owner OAuth or remote control.
TEST_VALIDITY: CI proves source; Worker HTTP health and OAuth deny verify deployment; owner-Claude UI discovery is independently tested by caller (initial 24 tools proven after reconnect), no spoof OAuth.
SCOPE: existing reviewed PR #218 only; lease metadata and safety diagnostics, no production runtime modification outside reviewed merge and official deploy workflow.
PEER_CHECK: GitHub main and GitLab main legacy bootstrap blob equal, index blob equal, reviewed branch head fixed.
