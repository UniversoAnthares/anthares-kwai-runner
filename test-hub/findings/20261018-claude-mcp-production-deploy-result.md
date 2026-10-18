# Claude Free MCP deployment – operational proof
STATUS: PARTIAL
AREA: ara-mcp-claude-deploy
DATE: 2026-10-18
RUN: Anthares Remote job 5a5d1f621bced12783e3535976e0086b
COMMIT: c4133032b21415b88ad3534cc9592d6b860019bc
SUPERSEDES: 20261018-claude-mcp-production-deploy-lease.md

## Production deployment
Cloudflare Worker anthares-ara-mcp deployed at https://anthares-ara-mcp.anthares1.workers.dev version 350b9bd5-ede4-4919-bc37-0d61b6718056. Previous rollback version 3b2a566b-ca6d-4b04-958d-3453ae4caad2. Exact PR #162 staging head used; no GitHub main merge. Wrangler deploy --keep-vars preserved production vars and secrets.

## Proof
- /health HTTP 200 with control_ready and device_connected.
- OAuth authorization-server and protected-resource discovery HTTP 200.
- Anonymous MCP tools/list HTTP 401.
- Forged Claude redirect authorization HTTP 400.
- Wrangler secret list confirms presence of ANTHARES_GITHUB_TOKEN and ARA_OAUTH_SECRET without disclosing values.
- No reboot or changes to CORTES, browser profiles or social publication.

## Remaining
Real owner OAuth connection from Claude Free, live tools/list verification, test GitHub read, branch edit, draft PR, and session refresh/replay QA. Full integration still PARTIAL. Setup link https://claude.ai/settings/connectors ; endpoint https://anthares-ara-mcp.anthares1.workers.dev/mcp ; choose Claude published client identity.