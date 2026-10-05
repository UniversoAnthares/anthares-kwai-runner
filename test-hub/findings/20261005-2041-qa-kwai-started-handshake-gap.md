# Kwai publish still lacks the central started handshake before irreversible publish
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: read-only audit
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1927-qa-kwai-publish-safety-static-proven.md; test-hub/findings/20261005-1955-queue-confirmation-invariants-proven.md
FAILED_AVOIDED: no real publication was triggered; no mutation was made under the active kwai-publish lease; Home return/toast are not treated as confirmation.
SUCCESS_SIGNAL: future publisher separates prepare from commit, records central publication_started immediately before the irreversible Publish action, requires a positive started response before the click, and routes every post-start ambiguity to UNCERTAIN.
FAILURE_SIGNAL: any path can click Publish while the central job still has publication_started=0, or a failed started call can continue to Publish.
TEST_VALIDITY: read-only code/lifecycle audit; this finding does not claim a live publication result.

## Resultado
The queue lifecycle intentionally requeues expired leased jobs when publication_started=0 and converts expired started jobs to UNCERTAIN. The current prepared Kwai publication module emits PUBLISH_REQUESTED and performs the irreversible Publish click inside the same Python process, without a central /started handshake immediately before that click. Therefore a runner crash after the click can leave the controller believing publication never started and can make the same job retry-eligible.

## Consequência
Before the real canary, split publication into prepare -> central started -> commit. The started call must fail closed before Publish. After started succeeds, crash/timeout/ADB loss must never blind-retry; reconcile from UNCERTAIN instead.
