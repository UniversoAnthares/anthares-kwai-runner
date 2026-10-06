# Lease: UNCERTAIN reconcile adversarial QA
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
LEASE_AREA: kwai-reconcile-qa
LEASE_EXPIRES: 2026-10-06T02:45:00Z
BASELINE_PROVEN: test-hub/findings/20261005-2112-kwai-reconcile-executable-proven.md
FAILED_AVOIDED: no publisher/commit invocation; no mutation of active kwai-publish files; no real publication.
SUCCESS_SIGNAL: five independent adversarial reconciliation invariants pass in parallel.
FAILURE_SIGNAL: any invariant permits confirmation without specific evidence or invokes publication.
TEST_VALIDITY: harness assertions must target current reconciler/verifier contracts; mismatch is HARNESS_INVALID, not product failure.
SCOPE: tests + dedicated QA workflow + append-only findings only.
