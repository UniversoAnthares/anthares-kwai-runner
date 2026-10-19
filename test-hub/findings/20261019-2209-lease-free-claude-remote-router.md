# Anthares free Claude Code — isolated remote runner lease
STATUS: RUNNING
AREA: ai-remote-claude-router
DATE: 2026-10-19
LEASE_OWNER: ChatGPT/free-claude-remote
START_UTC: 2026-10-19T22:09:30Z
EXPIRES_UTC: 2026-10-19T23:10:00Z
BASELINE_PROVEN: 20261019-1216-claude-mcp-real-acceptance-proven.md; 2026-10-06-ai-orchestrator-production-proven.md; Gemini/Bitwarden workflow run 39312615450 (real generation PASS).
FAILED_AVOIDED: OpenCode Free and MiMo unauthenticated public calls returned HTTP 403; do not assume public catalogs prove inference. No VPS, Render, paid providers, exposed ports, desktop dependency for cloud runner, or main direct edits.
SUCCESS_SIGNAL: PR CI static gate passes; owner-authorized GitHub Actions dispatch runs Claude Code with Gemini token from existing Bitwarden via loopback-only 9Router, two model fallback combos, logs ANTHARES_FREE_CLAUDE_RUN=PASS; for edit mode only scoped change and draft PR.
FAILURE_SIGNAL: missing Bitwarden secret, free-tier model failure, rejected invocation/permission, unsafe changed files, invalid credentials, or lack of real generation.
TEST_VALIDITY: pull_request static tests do not prove real model access. Do not mark PROVEN without actual authenticated GitHub Actions dispatch output. Record run SHA, job and decisive markers.
SCOPE: Add only a new workflow plus 3 new scripts/tests. Do not modify AI Hub, Bitwarden production sync, Cloudflare Workers, CORTES or WordPress.
PEER_CHECK: GitLab main .github/workflows enumerated; proposed workflow absent. Separate branch and draft PR; no blind cross-provider sync.

PROGRESS_2026-10-19_22:39Z:
- Run #39334979588: three current Gemini models PASS; 9Router JSON-only test failed on SSE HTTP 200.
- Run #39335532854: actual 9Router generation PASS, Claude Code reached max 8 agentic turns.
- Run #39336129062 at commit 48744cbd: Bitwarden, 3 free models, 9Router and actual Claude Code planning response PROVEN, cleanup PASS.
- NEXT: draft PR with one-file edit acceptance, plus explicit failover test where safe. This renewal applies only to those tests.
