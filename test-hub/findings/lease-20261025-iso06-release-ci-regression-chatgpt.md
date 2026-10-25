# Lease — CORTES-ISO-06 read-only hosted CI for signed review-intent gate
STATUS: RUNNING
AREA: architecture / iso06-signed-identity-ci-only
DATE: 2026-10-25
JOB: iso06-release-ci-20261025
COMMIT: clipper main db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none
LEASE_OWNER: ChatGPT Anthares Operations
LEASE_SCOPE: a new .github/workflows/network-release-identity-regressions.yml on existing platform/iso06-signed-release-authority-20261025 branch, only for tests/test_network_release_identity_gate.py and ci/network_release_identity_gate.py. No credential-scope CI workflow changes, no protected existing files, no publisher/queue/session/deploy/prod writes.
LEASE_START_UTC: 2026-10-25T21:32:00Z
LEASE_EXPIRY_UTC: 2026-10-25T22:02:00Z
BASELINE_PROVEN: existing release identity module + 23 fixture tests (PR #206); governance preflight f6fc9ca59a96e451 PASS and audit 218/0. Platform main remains unmodified. CI-01 credrefs workflow automation previously explicitly security-denied, not part of this scope.
FAILED_AVOIDED: excluded four suites, secret-scanning workflow previously denied; hosted runner allocation earlier failed before step for unrelated SHADOW-01, so lack of hosted runner is NOT_TESTED rather than code failure. Do not use Windows self-hosted fallback on untrusted PR code.
SUCCESS_SIGNAL: PR-scoped hosted workflow completed success with 23/23 and explicit deploy_authorized=false, no secret access. PR remains draft with no production promote.
FAILURE_SIGNAL: scoped regression failure, invalid identity gate, CI permissions spill, unexpected publication/deploy.
TEST_VALIDITY: exact workflow job+step logs and PR SHA required; no workflow run or runner=null => NOT_TESTED; green only with observed 23 PASS.
