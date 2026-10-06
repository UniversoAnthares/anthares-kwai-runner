# Lease kwai-publish UNCERTAIN reconciler
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T01:08:00Z

BASELINE_PROVEN: deterministic gallery matcher behavioral proof; specific account+title verifier; production control v14 queue/reconcile semantics.
FAILED_AVOIDED: generic freshness markers cannot confirm; PROFILE_LOADING/UNAVAILABLE cannot prove absence; no blind republish from UNCERTAIN; active kwai-login lease is independent and will not be mutated.
SUCCESS_SIGNAL: a dedicated reconcile path can only resolve UNCERTAIN to confirmed when the existing specific verifier produces account+title evidence; any absent/loading/unavailable/ambiguous result remains UNCERTAIN and never invokes publish.
FAILURE_SIGNAL: reconciler invokes kwai_publish_video commit/Publish, treats profile unavailability as absence, or releases a retry from ambiguous evidence.
TEST_VALIDITY: source/behavioral tests with stub verifier/controller; no Android/login/real publication.

## Objetivo
Implement the missing post-UNCERTAIN reconciliation path so a previously attempted job is searched and resolved without any possibility of republishing it blindly.
