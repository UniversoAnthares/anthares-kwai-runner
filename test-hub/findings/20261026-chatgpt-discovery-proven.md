# Existing ChatGPT connection receives actionable remote discovery
STATUS: PROVEN (server deployment, authenticated caller readback, project instruction persistence)
AREA: ara-mcp-capability-discovery
DATE: 2026-10-26
JOB: chatgpt-access-repair-20261026
COMMIT: ab5734da8520b5f859db67af5de65aff4d8c0438
SUPERSEDES: 20261026-chatgpt-discovery-running.md
LEASE_STATE: CLOSED
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1445
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40326561243

## Verified change
MCP 1.2.0 / discovery revision 2026-10-26.1 supplies guidance through existing capabilities and session_status responses and initialization instructions. Existing schemas and OAuth grants remain unchanged. Caller-scoped delegation metadata no longer implies ungranted github scopes.

41 local bridge/OAuth/security tests passed plus the authenticated discovery fixture. Canonical production run passed reviewed tests, propagation/version verification and anonymous MCP 401. Worker version d051db77-a06c-4213-a63e-087f225724a2.

Real existing ChatGPT-side capabilities call returned revision 2026-10-26.1, ara.read/ara.write and remote_execution=granted. Executing its exact returned discovery_command via the existing ARA connector completed job c825a91708623a37744f911cd88ad52e, exit_code=0, no timeout, empty stderr; Browser Hub, installed Codex bridge and launcher references were returned. No agent was started as an installation probe.

The owner's existing Anthares project instructions were preserved and appended with a short capability-discovery instruction. Browser UI Save completed; reopening settings returned the exact expected 7,959 characters including the addition. Extension-based browser control was therefore verified through the actual requested configuration change, without personal keyboard/clipboard. The job-owned temporary tab was closed in finally immediately after proof capture. Private screenshot and inventory remain outside public Git.

## Boundaries
This repairs discoverability of existing authorized routes. It does not install a separate Anthares Browser plugin, grant every account, enable administrator CDP, automatically control Work, transfer tools to unrelated chats, or guarantee future model behavior. Existing chats can receive the guidance on their next capabilities/session_status call; the project instruction is persisted, but model uptake by every already-running turn was not tested. The original CF-02/SEC-01 operations and their reported security denials were not retried. Production publisher/queue changes remain out of scope. No source or security bypass was used.

GitLab's independent main history was inspected and preserved; these gateway paths are absent there. No blind mirroring or force updates. Governance preflight version f6fc9ca59a96e451 and hashes are in the local job receipt.
