# Lease: ChatGPT + Claude Code + Work collaboration gateway
STATUS: RUNNING
AREA: anthares-multiagent-work-bridge
LEASE_OWNER: ChatGPT/multiagent-work-bridge
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/anthares-collab-work-20261020
START_UTC: 2026-10-20T01:39:11.683Z
EXPIRES_UTC: 2026-10-20T02:59:11.683Z
BASE_HEAD: 0e75711907e7bbe4dbc0afbb9143d6d38a876758
BASELINE_PROVEN: run 39352658418 Claude Free OAuth -> Cloudflare -> GitHub Actions Claude Code/9Router/Gemini -> result success and user confirmed get_claude_code_result ready:true; GitHub connector created owner issue #222, user.id 81930373.
FAILED_AVOIDED: do not modify production Cloudflare OAuth or secrets; do not bypass ruleset proteger-main; do not allow public issue authors to spend Github Actions/Gemini quota; do not auto-merge; do not claim Work API session can run without Work mode.
SUCCESS_SIGNAL: owner-only validated collaboration issue triggers one plan-mode Claude Code workflow from main, idempotent claimant and result link; CI parser tests, proven PR event and installation of shared source; ChatGPT and Work use GitHub issues; Claude uses existing Anthares MCP and new optional read tool.
FAILURE_SIGNAL: unauthorized actor can dispatch; tasks injection; duplicate dispatch; missing default-branch workflow due to blocked protected main; degraded OAuth.
TEST_VALIDITY: unit/PR CI on feature branch proves code only; production issue-created execution needs owner main merge then real canary to prove ChatGPT/Work->Claude Code path. Work session consumption must be separately observed.
SCOPE: tools/anthares_collab_*.mjs, .github/workflows/anthares-collab-*.yml and docs; optional low-risk MCP read interface via new file imported by github-bridge; no CORTES or WordPress edits.
PEER_CHECK: GitLab and GitHub tools trees read; collaboration targets absent. Open PR #218 changes index.js/legacy deploy unrelated; do not conflict.
LEASE_STATE: ACTIVE
