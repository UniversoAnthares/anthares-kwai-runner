# Lease amendment: concrete Threads destination reconciliation
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
JOB: r076-iso01-iso02-20261024
SUPERSEDES: test-hub/findings/20261024-2138-lease-r076-threads-account-scope-chatgpt.md
LEASE_AREA: cortes-threads-owned-inventory-ci
LEASE_OWNER: ChatGPT current conversation
LEASE_STATUS: ACTIVE
LEASE_EXPIRY_UTC: 2026-10-24T22:08:00Z

## Reason for scope correction
Read-only review of active code tools/cortes_threads_cloud_handoff.mjs on kwai-runner main found TARGET='threads:universoanthares', whereas historical social_api_publisher.py and social_adapters/direct_social.py default to threads:primary. These labels are not interchangeable without independent identity proof. Replace initially requested primary with the concrete active target threads:universoanthares; legacy threads:primary is an external shared route requiring separate reconciliation, not silently mapped or migrated.
Baseline and safety signals unchanged. Owner is organization UniversoAnthares; remote Threads Graph username, SID, OAuth grants and secrets are not inferred or copied.
Deliverable: exact threads:universoanthares code/execution/queue/token-reference owner map and a network-only documentation branch exercising existing trusted-base scope gate; no deploy or merge.
