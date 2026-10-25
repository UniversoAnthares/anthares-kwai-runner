# CORTES-ISO-06 — signed release intent gated CI: runner not allocated
STATUS: PARTIAL
AREA: architecture / iso06-signed-identity-ci-only
DATE: 2026-10-25
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40236892818
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40236892818/job/121300274615
COMMIT: 210543738648add2c0d929632e78ba015ef0cb30
SUPERSEDES: lease-20261025-iso06-release-ci-regression-chatgpt.md
LEASE_AREA: iso06-signed-identity-ci-only
LEASE_STATUS: CLOSED

## Implemented
PR https://github.com/UniversoAnthares/anthares-clipper/pull/206 (draft) now includes new only-when-changed .github/workflows/network-release-identity-regressions.yml, with read-only contents permission, persist-credentials=false, GitHub-hosted ubuntu-24.04, no secrets, no publisher, no OIDC requests, 7-day sanitized log artifact. Other workflows preserved.

## Actual run evidence
The GitHub Actions pull_request job 121300274615 concluded failure without any steps, with no runner_name, log (BlobNotFound) or artifacts. The actual 23-case suite NEVER ran on this hosted job; classify this as NOT_TESTED/HARNESS rather than test regression. Previously isolated Python 23/23 fixture tests were PASS with source blobs 9afd70ba5fd667766ad8cb8e2b3ea5d8fadb73ad and 09de0f96d068f6d4b13d70600f8dec7d4ac7a8b8. Scope PR check run 40236891033 was in progress at read; separate from hosted CI failure.

## Consequence
No automatic hosted regression acceptance, no provider IAM proof, no production release, no permission to migrate or deploy. A future trusted hosted runner allocation or genuinely sandboxed and independently fenced test lane is required; do not repeat the same failed harness without a causal change. Existing Windows self-hosted runner is NOT selected for executing untrusted PR-head code. Avoid security-denied Windows file mutations and CI-01 credential-scope workflow. Main services/credentials unchanged. Governance local f6fc9ca59a96e451 218/0; GitHub main 2e28d54043d6bad1 differs in INDICE; not overwritten.
