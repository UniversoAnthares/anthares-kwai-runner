# Actual Claude connector acceptance
STATUS: RUNNING
AREA: ara-mcp-claude-deploy, claude-session
LEASE_OWNER: codex-01a14ef0
EXPIRES_UTC: 2026-10-19T01:30:00Z
SUPERSEDES: 20261019-0059-claude-owner-github-oauth-deployed-partial.md
BASELINE_PROVEN: Worker89b087e4 sourcee97cb383;16 tests pass; live OAuth-start200/302; signed Remote preserved. Owner reports Claude login complete.
FAILED_AVOIDED: missing sender domain bypassed by official GitHub identity with no repo scopes; no credentials in logs; no changes to CORTES or personal profiles.
SCOPE: isolated browser connector approval and real Claude MCP read/edit/draft acceptance. No arbitrary shell exposure or publication controls.
SUCCESS_SIGNAL: actual Claude tools list and calls, disposable claude/* commit and draft PR independently verified.
FAILURE_SIGNAL: wrong identity, lost browser binding, missing scope, credential failure, rejected stale head or concurrent lease.
TEST_VALIDITY: fresh source/peer/current deployment; mocks not accepted as Claude proof; acquire bridge lease before GitHub write.
