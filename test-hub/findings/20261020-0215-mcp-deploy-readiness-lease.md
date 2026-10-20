# Claudecode MCP production deploy propagation guard
STATUS: RUNNING
AREA: claude-mcp-deploy-readiness
LEASE_OWNER: ChatGPT/claude-mcp-deploy-readiness
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/mcp-deploy-readiness-guard-20261020
START_UTC: 2026-10-20T02:14:14.686Z
EXPIRES_UTC: 2026-10-20T03:04:14.686Z
BASE_MAIN_HEAD: c8ffa82ff1a0dec517349fa38cae099a1ce8717a
BASELINE_PROVEN: Claude Free→Claude Code 39352658418 owner ready=true; ChatGPT→Issues→Claude Code 39356635285 success. Version 1.1.0 and all delegated tools independently observed live in /health after PR #218 merge.
OBSERVED_FAILURE: Production deploy run 39357593535 deployed Worker but post-deploy test exited 1 at 02:12:09 UTC, less than 1s after deploy; independent /health later confirmed version 1.1.0, tools list and Github OAuth. Legacy ara-mcp-email-otp-deploy.yml still listens to index.js and failed preflight on same push (39357593404); fail closed but creates conflicting deploy path.
FAILED_AVOIDED: never redeploy legacy OTP workflow; never change OAuth tokens/owner credentials; no force push; preserve Anthares CORTES, Work, GitHub and Claude direct paths.
SUCCESS_SIGNAL: legacy email OTP workflow is manual-only and refuses production GitHub-owner OAuth; canonical deploy waits for version/schema and owner health across propagation before returning success; CI static + live full guarded deploy success; anonymous MCP 401 confirmed.
FAILURE_SIGNAL: old email OTP workflow deploys, GitHub owner identity changes, health/version remains unavailable, CI fails or 403/401 regressions.
TEST_VALIDITY: mocked/dry-run tests cannot prove Cloudflare health; canonical real post-merge deploy must pass with exact version and tool list. Check no overlapping deployment executor before merge.
PEER_CHECK: Github/GitLab legacy email source blob equal. GitLab main deploy workflow blob 07f5618f490d447316b836d6a4a4cd2411e2a20f; compare/retain provider diffs explicitly, no blind mirror.
SCOPE: .github/workflows/ara-mcp-email-otp-deploy.yml; .github/workflows/anthares-claude-code-mcp-deploy.yml; relevant CI; Test Hub.
