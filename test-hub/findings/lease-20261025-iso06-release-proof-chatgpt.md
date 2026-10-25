# CORTES-ISO-06 — release identity proof: test lease
STATUS: RUNNING
AREA: architecture / iso06-release-authority-offline
DATE: 2026-10-25
RUN: none
JOB: iso06-release-proof-20261025
COMMIT: anthares-clipper main db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none
LEASE_OWNER: ChatGPT Anthares Operations
LEASE_SCOPE: add ci/network_release_identity_gate.py and tests/test_network_release_identity_gate.py on separate platform/iso06 release branch. No CI workflow, existing publisher, session, IAM, production queue, DB, secrets, environment or deployment altered.
LEASE_START_UTC: 2026-10-25T21:14:29Z
LEASE_EXPIRY_UTC: 2026-10-25T21:44:29Z
BASELINE_PROVEN: governance preflight f6fc9ca59a96e451 passed; audit 218/0. GitHub governance main 2e28d54043d6bad1, index divergent; preserve both. Legacy shared social matrix with secrets for Instagram/Threads/X still active.
FAILED_AVOIDED: explicit security denial on CI-01 credential-reference workflow, protected Windows ACL changes, excluded four test suites; no alternate-channel workaround. Separate from the RUNNING CI-01 credential-scope lease.
SUCCESS_SIGNAL: new independent fail-closed release authorization library and tests passing on a genuine Python runtime, cross-network mismatch denied with recorded evidence, reviewed draft PR; no deploy permission granted.
FAILURE_SIGNAL: stale HEAD, competing lease, blocked provider action, untrusted OIDC claims, test failures.
TEST_VALIDITY: synthetic identity assertions are unit tests, NOT authorization from the real provider. No live publication or production mutation. Final status PARTIAL unless actual provider negative IAM test is performed by authorized independent principals.
