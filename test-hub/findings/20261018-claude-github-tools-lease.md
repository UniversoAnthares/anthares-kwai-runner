# Claude Free GitHub draft-only MCP tools
STATUS: RUNNING
AREA: claude-github-tools
DATE: 2026-10-18
LEASE_OWNER: ChatGPT/claude-free-stage2
START_UTC: 2026-10-18T17:55:43.431Z
EXPIRES_UTC: 2026-10-18T18:24:43.431Z
BASELINE_PROVEN: draft PR #162; main 3a969e7264c841bebe221de9dcdca9bdfb0b8d3e; GitLab peer main separate history; GitHub Actions and GitLab pipelines no running jobs.
FAILED_AVOIDED: avoid exposing unrestricted Windows control and GitHub main write to third-party clients; no paid Claude Code, no secrets in Git.
SCOPE: add fail-closed GitHub MCP API module on branch integration/claude-free-mcp-20261018, with repo allowlist, Claude branch restrictions, exact SHA/HEAD, Test Hub lease, draft PR; no deployment/merge or production write.
SUCCESS_SIGNAL: isolated code and negative test suite, PR #162 updated; verification of no production change.
FAILURE_SIGNAL: bypass default-branch or allowlist, unsigned/wrong scope write, stale SHA accepted.
TEST_VALIDITY: each write checks HEAD and source file SHA, peer source comparison, no external live publication or unauthenticated GitHub token access.
SUPERSEDES: 20261018-claude-free-mcp-staged-partial.md
