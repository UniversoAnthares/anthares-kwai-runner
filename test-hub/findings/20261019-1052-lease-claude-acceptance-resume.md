# Resume Claude OAuth interoperability and actual acceptance
STATUS: RUNNING
AREA: ara-mcp-claude-deploy, claude-session
LEASE_OWNER: codex-01a14ef0
EXPIRES_UTC: 2026-10-19T11:20:00Z
SUPERSEDES: 20261019-0101-lease-claude-real-acceptance.md
BASELINE_PROVEN: liveWorker89b087e4, branchb7bd1848 with16 tests plus capabilities pass; Remote connected, queue empty. GitHub main6e407ce1 has unrelated publication findings. Owner completed Claude login.
FAILED_AVOIDED: actual browser POST origin null due no-referrer fixed by same-origin HTML policy; initial MCP challenge omitted GitHub scopes, now advertises full supported set. Prior interrupted deployment did not publish these fixes; production version independently verified before retry.
SCOPE: guarded keep-vars deploy of already tested interoperability correction; real isolated Claude owner OAuth and disposable branch/draft PR acceptance. Preserve CORTES, Android, existing keys and ChatGPT.
SUCCESS_SIGNAL: live correct challenge/form, real owner callback, Claude tools list/read/write/draft PR independently verified.
FAILURE_SIGNAL: changed deployment/source, lost identity/browser binding, unsupported scope, competing lease or credential failure.
TEST_VALIDITY: no simulated call counts as Claude proof; no production deploy as audit probe; inspect source and peer before deploying intended reviewed correction.
