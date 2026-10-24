# CORTES F1 — lease de implantação independente Google Drive
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
LEASE_OWNER: chatgpt-cortes-drive-f1-20261024
EXPIRES_UTC: 2026-10-24T17:14:00Z
RUN: Anthares Remote jobs ef3b4717a902d0f03d920ce5267c4f40, 5132ff7eb3bd3f18cb9fac70e8f07b87
JOB: cortes-google-drive-f1-activation
COMMIT: anthares-clipper feature/cortes-cloud-drive-replication-20261023 @ 85e903c93f4cc85bace4e07cbb5f2e705fbd9792
SUPERSEDES: none
SCOPE: Google Drive two-account replica sidecar and Windows scheduler only; no publishers, Neon queue, social login, or cloud migration merge.
BASELINE_PROVEN: dedicated independent OAuth clients for profile3 and profile9; Windows SYSTEM preflight ready_count=2, both remote_probe=ok; 96-byte SHA-256 canary verified previously; staging replica guard existing; runner-media output/shorts directories empty.
FAILED_AVOIDED: shared rclone client 403 rateLimitExceeded; avoid profile2; preserve local originals; never equate green idle to backup; do not merge draft PR #190.
SUCCESS_SIGNAL: independent scheduled task runs in SYSTEM; ledger records 2 SHA-256-verified replicas for eligible controlled test media; readback/restore checked; retry after controlled failure without duplicate/unsafe deletion.
FAILURE_SIGNAL: credentials unavailable to SYSTEM; lease conflict, stale lock, source absent, one remote fails, hash mismatch, unexpected task/publication interference.
TEST_VALIDITY: synthetic fixture tests are marked synthetic; actual production master backup requires real eligible media and cannot be inferred from canary.
