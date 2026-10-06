# Lease queue: production self-test through Kwai GitHub OIDC identity
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: queue-self-test
COMMIT: pending
SUPERSEDES: none

LEASE_AREA: queue
LEASE_EXPIRES: 2026-10-06T00:34:00Z

BASELINE_PROVEN: test-hub/findings/20261005-2117-cloudflare-v12-production-proven.md; test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md; Worker selfTest uses isolated `__selftest__` platform and cleans generated jobs in finally.
FAILED_AVOIDED: do not enqueue/lease real Kwai jobs for integration testing; do not add a new workflow to the OIDC allowlist; use the already-allowlisted `kwai-real-publish.yml` identity in an explicit safe diagnostic mode. Real publication remains quarantined.
SUCCESS_SIGNAL: GitHub Actions workflow `kwai-real-publish.yml` obtains OIDC, POSTs `/queue-self-test`, receives HTTP success with `ok=true` and all declared queue invariants true, while no Publish/Android action is invoked.
FAILURE_SIGNAL: OIDC rejected, self-test HTTP/JSON failure, or any invariant false.
TEST_VALIDITY: workflow source must visibly branch into queue-self-test mode before the real-publication guard; the test must not receive or use a media URL or invoke Android/Kwai publication code.

## Objetivo
Prove that production v12 accepts the exact GitHub OIDC workflow identity needed by the Kwai publisher and that the production Durable Object lifecycle invariants execute successfully in its isolated self-test namespace.
