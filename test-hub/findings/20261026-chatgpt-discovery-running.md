# ChatGPT remote capability discovery repair
STATUS: RUNNING
AREA: ara-mcp-capability-discovery
DATE: 2026-10-26
JOB: chatgpt-access-repair-20261026
OWNER: codex
LEASE_SCOPE: cloudflare-ara-mcp discovery metadata, its tests and canonical deploy validation only
LEASE_BASE_HEAD: 0d74f8ce117378f5d91cf3b9e3d484394d4f5d71
LEASE_EXPIRES_UTC: 2026-10-26T15:00:00Z
SUPERSEDES: none

BASELINE_PROVEN: current ARA capabilities/session_status calls work; installed ChatGPT app permission is Allow all actions. Existing capabilities omit operational discovery. GitHub index blob 7513b2186408a3da2c136e1358969fe2e98e3949; deploy workflow af3d66aeee6d9244756043bfd478e7b03e4a57f7. GitLab main 9edcf24e lacks these paths; preserve independent history, no blind mirror. No relevant deployment running at preflight. Governance f6fc9ca59a96e451 delivered, hashes in central job receipt; no private inventory published.
FAILED_AVOIDED: no OAuth grant widening, no administrator CDP enablement, no retry of screenshot-reported security refusal, no personal browser input, no changes to publishing or other agents.
SUCCESS_SIGNAL: current-client scopes and actionable discovery returned by existing capabilities/session_status; initialize instructions; real isolated browser interaction and cleanup; canonical guarded deployment plus authenticated caller readback.
FAILURE_SIGNAL: incorrect writable claim for read-only client, removed tool/auth regression, private inventory leakage, owned tab not closed, missing deployed revision.
TEST_VALIDITY: fixture tests verify scope filtering; live calls verify actual transport. Resource discovery never implies service login or full access in unrelated chats. Old schemas remain compatible so existing callers can receive new guidance without new tool registration.
