# Final Claude deployment and merge
STATUS: RUNNING
AREA: ara-mcp-claude-deploy / claude-session
LEASE_OWNER: codex-01a14ef0
START_UTC: 2026-10-19T18:42:00Z
EXPIRES_UTC: 2026-10-19T19:10:00Z
SUPERSEDES: 20261019-1220-lease-claude-final-integration-tests.md
BASELINE_PROVEN: actual current UTC refreshed; integration branch 30217080974912cbfc049072b844f473a69c0e27; previous Worker 24ffad76-20a0-4911-b6c9-465ad1b135b2
FAILED_AVOIDED: earlier lease carried stale session time and is invalid for this resumed round; rerun checks under this lease before deployment. Preserve concurrent main, secrets and ChatGPT; no unrestricted Claude shell.
SUCCESS_SIGNAL: reviewed fixed suite passes, deployed source pin matches, actual Claude run_tests succeeds, PR162 merged with expected HEAD, health/auth regression preserved
FAILURE_SIGNAL: concurrent source/deployment, failing tests, wrong test source or auth regression
TEST_VALIDITY: actual-time lease, fresh refs and real end-to-end evidence required
SCOPE: MCP integration only. No CORTES, Android, SSH or publication changes.
