# Anthares Claude Free to GitHub Claude Code bridge
STATUS: RUNNING
AREA: claude-mcp-code-delegation
LEASE_OWNER: ChatGPT/claude-mcp-code-delegation
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/remote-code-dispatch-20261019
START_UTC: 2026-10-19T23:51:00Z
EXPIRES_UTC: 2026-10-20T01:51:00Z
BASELINE_PROVEN: test-hub/findings/20261019-2308-free-claude-autopr-proven.md; test-hub/findings/20261019-1848-claude-final-merge-and-approved-tests.md; Claude MCP OAuth accepted in real owner session, GitHub Actions Claude Code plan/edit/fallback and draft PR proven separately.
FAILED_AVOIDED: no arbitrary Windows command; no direct main edits; no unreviewed prompt execution via Cloudflare; no paid providers/VPS; do not auto trigger retired Email OTP bootstrap workflow.
SUCCESS_SIGNAL: reviewed bridge passes mocked REST tests, GitHub workflow validates user request correlation and stored artifact, protected MCP tools/list and access, Cloudflare deploy with real owner OAuth, owner Claude calls run_claude_code then status/result and receives real generated response.
FAILURE_SIGNAL: GitHub Cloudflare secret lacking Actions:write; missing OAuth permission or unavailable Claude quota; GET artifact cannot be decoded; CI/deploy failure; token exposure or unintended production mutation.
TEST_VALIDITY: CI and unauthenticated HTTP checks prove code only; real owner Claude invocation plus live workflow response required for PROVEN end-to-end.
SCOPE: cloudflare-ara-mcp/src/github-bridge.mjs and isolated new module/tests; free Claude workflow and tests. Use branch and PR; preserve existing Cloudflare OAuth, ChatGPT, CORTES, WordPress, secrets.
PEER_CHECK: GitLab peer read of current github-bridge.mjs matched GitHub blob; search found no existing run_claude_code. No concurrent Claude-MCP run observed.
