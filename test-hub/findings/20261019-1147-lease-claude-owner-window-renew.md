# Fresh owner authorization window requested
STATUS: RUNNING
AREA: claude-session, ara-mcp-claude-deploy
LEASE_OWNER: codex-01a14ef0
EXPIRES_UTC: 2026-10-19T12:15:00Z
SUPERSEDES: 20261019-1105-claude-oauth-interoperability-and-branch-fencing-partial.md
BASELINE_PROVEN: deployedWorker13f5ee1d source5306fbf2;19 tests and signed control pass. Prior acceptance lease closed. Owner requests a regenerated authorization window after an error; browser currently about:blank.
FAILED_AVOIDED: do not reuse expired ten-minute transaction; do not remove GitHub visibility protection or manipulate focus; preserve credentials and dedicated profile.
SCOPE: create fresh legitimate connector authorization using the isolated Anthares Browser, leave its GitHub owner-consent page for the owner. No code/deploy or CORTES change.
SUCCESS_SIGNAL: fresh OAuth flow reaches correct GitHub owner application with Public data only, then actual owner callback and Claude tool acceptance if completed.
FAILURE_SIGNAL: missing login, wrong identity, policy-denied window creation or actual OAuth error.
TEST_VALIDITY: distinguish navigation/loading errors from OAuth failure; never log callback code/state/cookies.
