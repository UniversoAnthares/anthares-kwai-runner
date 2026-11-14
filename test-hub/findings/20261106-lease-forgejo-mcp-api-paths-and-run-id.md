# Forgejo MCP public API read compatibility — scoped lease
STATUS: RUNNING
AREA: forgejo-mcp-readonly
DATE_UTC: 2026-11-06T00:05:00Z
EXPIRES_UTC: 2026-11-06T01:05:00Z
OWNER: chatgpt-aoi4-forgejo-api-20261106
BASE_HEAD: ba6ffe983a2112014db7926cf0bd6c39a1ea6061
BASELINE_PROVEN: Forgejo v15.0.9 public /api/v1/repos/anthares-admin/anthares-kwai-runner/actions/runs?limit=5 HTTP 200, percent-encoded owner%2Frepo URL HTTP 404; UI run #1 mapped to API run id=567 by direct read.
FAILED_AVOIDED: do not rerun workflow #1; do not change runners, production writers, secrets, OAuth grants or social publication; no server-side admin operation or bypass.
SUCCESS_SIGNAL: minimal read-only Forgejo bridge fix preserving owner/repo slashes and UI run mapping; dedicated regression test; draft PR with URLs and SHAs; no production deploy without verified approval.
FAILURE_SIGNAL: stale SHA, active competing lease, regression fail, denied GitHub mutation, or unexpected provider API behavior.
TEST_VALIDITY: direct public Forgejo read probes independently validate the two URL forms; synthetic tests validate routing only.
SCOPE: cloudflare-ara-mcp/src/forgejo-bridge.mjs and cloudflare-ara-mcp/forgejo-forwarding.test.mjs; append-only finding.
COST: zero new providers or paid quota. ROLLBACK: abandon draft branch; preserve production and runner.
