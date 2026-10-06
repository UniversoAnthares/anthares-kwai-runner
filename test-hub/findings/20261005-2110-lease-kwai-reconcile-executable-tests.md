# Lease kwai-publish executable uncertain reconciliation tests
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: kwai-publish
COMMIT: pending
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T01:30:00Z

BASELINE_PROVEN: v16 publisher adapter and observation-only reconciler static invariants.
SUCCESS_SIGNAL: executable fixtures prove positive verification reconciles exactly once; verifier failure, missing proof, or central rejection stay UNCERTAIN; no publisher/commit invocation exists.
FAILURE_SIGNAL: any ambiguous case confirms, any failed central ACK confirms, or test can invoke publish.
TEST_VALIDITY: local GitHub Actions fixture behavior only; no Android and no real publication.
