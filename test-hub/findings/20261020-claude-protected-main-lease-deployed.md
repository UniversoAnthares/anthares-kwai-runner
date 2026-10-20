# Claude protected-main lease repair deployed
STATUS: PROVEN (patched GitHub API flow and production deployment); CLAUDE_UI_ACCEPTANCE: NOT_TESTED
AREA: claude-github-tools
DATE: 2026-10-20
SUPERSEDES: 20261020-claude-protected-main-lease-partial.md; 20261020-claude-protected-main-lease-running.md
LEASE_STATE: CLOSED
COMMIT: c34f8e602a633aaa6491c08addfc7ba9c639e362
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/254
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39438241455
WORKER_VERSION: 5259bce5-b430-48f9-afea-2f911bd71cbf

Main requires PRs, while old begin-task wrote its lease directly to main. Expired legacy lease did not explain this path. Fix preserves branch protection and OAuth, registers leases on test-hub/claude-github-leases with exact atomic expectedHeadOid and committed read-back, and checks both legacy/new leases. Safe explicit branch-protection error classification added.

Real patched-module API flow using owner CLI credential completed begin-task, create-branch, put-file and draft PR #253, with protected main unchanged. Disposable test PR must not merge. Owning acceptance lease closed append-only on coordination ref at commit d81b978c9d49827959fd65c1797430a90455af25, so no lingering test reservation blocks Claude.

PR CI 39438094685: bridge suite 30/30; workflow tests 8/8; actual Worker bundle PASS. Normal protected PR merge #254 succeeded at c34f8e6. Official deployment 39438241455 passed 36/36 security/OAuth/bridge tests, preserved required secrets, verified owner GitHub auth and control_ready, deployed Worker 5259bce5-b430-48f9-afea-2f911bd71cbf, verified anonymous MCP 401 and deployment acceptance. Final independent /health: ok=true, oauth=true, mcp=true, control_ready=true, oauth_owner_code_mode=github_owner_identity, mcp_server_version=1.1.0.

Actual Claude browser conversation was not invoked; user may now repeat the original test. Do not confuse local owner-token API proof with a production OAuth-scoped Claude tool invocation. No main rule weakening, credential rotation, unrelated production publication or legacy OAuth change.
