# GOV-14: cloud-first guard runner capability probe (coordination lease)
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
JOB: R076-GOV14-20261024
LEASE_OWNER: chatgpt-gov14
COMMIT: anthares-clipper main 8bdadaac9370c709b0fdfaa12667bb992a5ca08e
SUPERSEDES: none
TARGET: UniversoAnthares/anthares-clipper/.github/workflows/network-scope-guard.yml (READ ONLY in this phase)
SCOPE: proposed self-contained, secret-free GitHub-hosted regression probe; no publishing, deploy, credential rotation, OS ACL or production queue mutation.
BASELINE_PROVEN: scope guard in trusted base passed GitHub Actions run 40115675447 on self-hosted Windows. Windows is owner's mandatory last executor when an equivalent cloud runner is proven.
FAILED_AVOIDED: do not change active guard runner before independently proving hosted CI capacity, and do not execute four tests previously explicitly refused by security controls.
SUCCESS_SIGNAL: a new hosted Ubuntu workflow builds from main and executes only the 23 already-authorized scope unit tests, with actual runner allocation, exit code zero and validated artifact/log.
FAILURE_SIGNAL: hosted queue/permission/quota failure or any of the authorized tests failing. No production effect on failure.
TEST_VALIDITY: cloud probe runs no publisher, secrets, browser sessions, code from untrusted PR heads, or existing denied tests; workflow configured read-only permissions.
GOVERNANCE_PREFLIGHT: f6fc9ca59a96e451 (D:\\AntharesWork\\anthares-clipper and D:\\AntharesWork\\anthares-kwai-runner); policy.py audit 218 repos, 0 failures.
NEXT: create separate PR on platform/* branch and only merge after review; record completion/blocked state in append-only finding and update Checklist R07.6.
