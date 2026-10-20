# MCP 1.1.0 cloud deployment and Work-ready collaboration handoff
STATUS: PROVEN (MCP production + GitHub queue); WORK_SESSION: NOT_TESTED
AREA: claude-mcp-deploy-readiness / anthares-multiagent-work-handoff
DATE: 2026-10-20
SUPERSEDES: test-hub/findings/20261020-0215-mcp-deploy-readiness-lease.md; test-hub/findings/20261020-0213-lease-claude-mcp-catalog-resume.md; test-hub/findings/20261020-0038-lease-claude-mcp-catalog.md (MCP catalog rollout)
PR_CATALOG: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/218
PR_GUARD: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/233
DEPLOY: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39358082325
INITIAL_PARTIAL_DEPLOY: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39357593535
LEGACY_SAFE_FAILURE: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39357593404
WORK_HANDOFF: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/234
WORK_SESSION: NOT_TESTED
LEASE_STATE: CLOSED AFTER VERIFIED PRODUCTION DEPLOY AND WORK HANDOFF

## Production evidence
- PR #218 merged normally after ruleset proteger-main stopped blocking all main updates while keeping protection against non-fast-forward/deletion and PR rule. Commit c8ffa82ff1a0dec517349fa38cae099a1ce8717a includes Worker MCP serverInfo version 1.1.0 and GET /health mcp_delegation_tools name list.
- Its reviewed deploy run 39357593535 published successfully but post-deploy health check exited code 1 too early (<1s after Cloudflare deploy): unrelated to actual OAuth 401, real generated code or missing tools. Independent later /health returned OAuth GitHub owner, control_ready, MCP 1.1.0 and three expected delegation tools.
- Legacy `.github/workflows/ara-mcp-email-otp-deploy.yml` auto-triggered on same index.js push and failed *before* deployment at retired oauth_owner_code_mode email_otp validation, run 39357593404. No evidence this workflow replaced production. PR #233 now makes legacy Email OTP manual-only. The previously separate stateless Email OTP workflow was also made manual-only in PR #218.
- PR #233 merged 2026-10-20 (commit ce165e1261a33516501460133f2144407df55a66), adds Cloudflare propagation wait for complete new version and exact tool names before declaring readiness.
- **Real post-merge run 39358082325 completed success**, all build/secrets/owner OAuth/Cloudflare deployment checks passed. Log: `ANTHARES_CLAUDE_DEPLOY_READY_ON_ATTEMPT=1`, `ANTHARES_CLAUDE_NEW_TOOLS_LIVE=PASS`, `ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS`, `ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS`. Deployed Worker version `73955dde-c827-4983-b110-032953918e6f`.
- Independent Cloudflare GET /health after deployment: ok=true, oauth=true, mcp=true, control_ready=true, oauth_owner_code_mode=github_owner_identity, mcp_server_version=1.1.0, mcp_delegation_tools=(run_claude_code, get_claude_code_status, get_claude_code_result). No credentials were read/printed.
- GitHub main push corresponding to merge PR #233 ran the *canonical* MCP deploy plus mirrors; **no Email OTP auto-deploy run** triggered.
- Source contract smoke PR #233 CI run 39357989082 success, includes assertions legacy push disabled and reviewed MCP catalog availability wait; normal reviewed merges, no forced changes to protected main.

## Multiagent shared queue and Work
- Production ChatGPT→Issue #230→Actions→Claude Code real plan proof remains run 39356635285 success and artifact #12235437781 with ANTHARES_COLLAB_CHATGPT_WORK_OK; direct Claude Free owner→Anthares→Claude Code remains independently proven run 39352658418 with user confirmation.
- New Work handoff issue #234 was created via authenticated GitHub connector, explicitly marked `READY_FOR_WORK / WORK_SESSION_NOT_TESTED`. It asks the Work app to review issue #230, run artifacts and OAuth health and publish an evidence comment or reviewed PR. This is a prepared, **not executed**, Work session.
- Production Claude Free MCP now includes `collab_get_task`, `collab_list_tasks` read-only code deployed by previous PR #226; concrete owner-Claude conversation call of these specific new tools still unverified. Existing direct 3 Claude Code tools WERE verified by user.
- Do not claim Work ran, or that Claude Free UI reloaded the additional read-only catalog entries without an actual client call. ChatGPT Work cannot be initiated or controlled by an undocumented Work API from ordinary Chat mode; the owner must select Work and let it access GitHub.
- Preserve public repository privacy limitations, quotas of GitHub/Gemini, Test Hub lease and PR-only edits, and rejection of duplicate task claims.

## Owner acceptance remaining
1. Work: initiate real ChatGPT Work session with GitHub connected, open owner issue #234 and leave a distinct review result. This is the only missing Work-specific active lane.
2. Claude Free: in owner session, refresh Anthares connector catalog if needed, call `collab_get_task(repo=UniversoAnthares/anthares-kwai-runner,issue_number=230)` and observe the real issue and completion events.
