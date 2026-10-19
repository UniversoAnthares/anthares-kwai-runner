# Claude OAuth email recovery
STATUS: RUNNING
AREA: ara-mcp-claude-deploy
LEASE_OWNER: codex-01a14ef0
EXPIRES_UTC: 2026-10-19T01:12:00Z
BASELINE_PROVEN: production350b9bd5 PR162 c4133032, Remote operational; prior deploy lease closed.
FAILED_AVOIDED: inspect exact Cloudflare error before retry; preserve PKCE, pinning, keys, ChatGPT and CORTES.
SUCCESS_SIGNAL: owner OAuth, MCP discovery and real isolated Claude GitHub read/write/draft PR.
FAILURE_SIGNAL: weakened identity, replay accepted, concurrency or service regression.
TEST_VALIDITY: check source, peer and deployed snapshot; synthetic requests cannot prove Claude acceptance.
SUPERSEDES: 20261018-claude-mcp-production-deploy-result.md
