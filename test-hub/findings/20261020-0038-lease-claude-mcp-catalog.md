# Claude Anthares: MCP tool discovery refresh / catalog proof
STATUS: RUNNING
AREA: claude-mcp-tool-discovery
DATE: 2026-10-20
LEASE_OWNER: ChatGPT/mcp-catalog-20261020
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/refresh-mcp-tool-catalog-20261020
START_UTC: 2026-10-20T00:37:52Z
EXPIRES_UTC: 2026-10-20T01:37:52Z
BASE_HEAD: a1bbe54ea865c33df033b3f973f79cd40afcf4df
BASELINE_PROVEN: test-hub/findings/20261020-0005-claude-mcp-delegation-deployed-partial.md. PR #214 deployed Worker dc6408ba-02fa-4ab5-a439-1760d3ec571e; new tools in github-bridge; CI 39345229461 passed.
OBSERVED_FAILURE: Real Claude Free owner's existing connected session still lists old 20 MCP tools and cannot discover run_claude_code, get_claude_code_status or get_claude_code_result. Existing index.js reports MCP serverInfo.version=1.0.1 and tools.listChanged=false.
FAILED_AVOIDED: Do not forge OAuth or bypass Claude approval, do not expose tokens, do not enable unsupported MCP notifications, do not run obsolete Email OTP deploy over GitHub-owner OAuth.
SUCCESS_SIGNAL: Worker GET /health explicitly reports current catalog schema and three tool names, version-bumped MCP initialize, CI tests and guarded deploy pass; after refresh of Claude connector owner-visible tools/list sees all three. Full remote run remains distinct acceptance.
FAILURE_SIGNAL: tools absent in compiled Worker, Cloudflare deploy failure, OAuth/anonymous restrictions regressed, client does not refresh even after reauthorization.
TEST_VALIDITY: health/catalog proves server publication only; owner Claude UI tool discovery is necessary to mark end-to-end PROVEN.
SCOPE: cloudflare-ara-mcp/src/index.js and isolated CI tests; protect legacy Email OTP auto-deploy from overwriting canonical GitHub OAuth; no changes to CORTES/WordPress/secrets.
PEER_CHECK: GitLab main blob equality of legacy bootstrap and index verified; no concurrent project mutations known.
