# Lease — Hostinger C8 protocol reconciliation
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / c8-hostinger-integration
DATE: 2026-10-29
OWNER: Work item5-hostinger-c8-20261029
LEASE: expires 2026-10-29T19:21:00Z; only PR1808 integration sources/tests/docs. No production deployment.
COMMIT: 23f9184046b4170cb5085148a284fe611f5e40da
SUPERSEDES: none
## BASELINE_PROVEN
Read PR1808 source, findings Stage A/B/C, main findings and Actions (all relevant PR1808 runs completed; no competing run).
GitLab peer 87307248 has no feature branch (404); main read at ffe437d02911bd5b9fc2f9cf6d29889d0684827a. No mirroring.
Hostinger deployed PHP read via existing SSH after authenticated hPanel File Manager failed ERR_CONNECTION_RESET twice.
Broker SHA256 537c6dfc5b54163b9a1cd7180e21dba21ca3bca05e5a33b236e0e2dbfe5b649c.
## FAILED_AVOIDED
No unsupported WSS/HMAC assumptions: actual broker is HTTPS JSON health/wait with listener role credential independent of publisher and device bearer.
Preserve Neon polling2s fallback, safety scan12s, heartbeat60s, leases/idempotency/global semaphore. No publisher/production/broker/secret changes.
## SUCCESS_SIGNAL
Exact broker protocol implemented and negative/positive contract tests and Windows build pass in external CI; live read-only health/wait matches parsed contract.
## FAILURE_SIGNAL
HEAD drift, competing lease, protocol mismatch, credential/redirect leakage, regression, quota.
## TEST_VALIDITY
Offline tests/Windows cross-build do not prove installed C8 or full post-INSERT roundtrip. Feature remains default OFF.
Governance SHA256: REGRAS CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138; INDICE 2EFAB2052ABDD9083FAB5DA6E489846E0AA75C7A8097C576AAE5D0BDE0A69D12; PROMPT BF5967D3D36854AA9FD3AC7831D26FE67933BDF995476091DC4F4A1CA6EA69BE.
