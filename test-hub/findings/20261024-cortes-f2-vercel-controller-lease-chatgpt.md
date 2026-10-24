# Test Hub — F2 controller Vercel contract alignment
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
RUN: none — no GitHub Actions
JOB: cortes-f2-vercel-controller-20261024
COMMIT: anthares-clipper/95f8ba5f1896149299694a626c7365d04bf65973
SUPERSEDES: none
OWNER: ChatGPT
GOVERNANCE_VERSION: 6276158ef2239898
SCOPE: Only tools/cortes_cloud_neon_controller.py and tests/test_cortes_cloud_neon_controller.py on feature/cortes-cloud-drive-replication-20261023; no publicadores, releases, production Neon or social jobs.
LEASE_DURATION: 30 minutes from this finding, expires automatically; other changes require their own coordination.
BASELINE_PROVEN: 006 Neon QA permits vercel_sandbox; manual QA Vercel FFmpeg->Neon SHA artifact_verified was documented, yet Python controller provider allowlist omits vercel_sandbox.
FAILED_AVOIDED: No Codeberg push retry after Forbidden; no paid Northflank/GitLab jobs; no rclone OAuth shared promotion.
SUCCESS_SIGNAL: Python controller accepts vercel_sandbox consistently with staging SQL and retains rejection of unknown/github_actions; tests and proof recorded separately.
FAILURE_SIGNAL: branch changed concurrently, invalid lease, failed test, unsafe shared-file modification.
TEST_VALIDITY: compare GitHub file blob SHA and feature HEAD immediately before editing; verify peer GitLab branch (previously absent), preserve existing code; emit follow-up finding.
