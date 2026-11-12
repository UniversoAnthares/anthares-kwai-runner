# RET-CI-209 + F1 revision proposal — coordination lease
STATUS: RUNNING
AREA: retention-ci-f1-review
DATE: 2026-10-26
RUN: none
JOB: RET-CI-209-20261026
COMMIT: anthares-clipper main db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none

## Scope
Owner ChatGPT. Expiration: maximum 30 minutes from this lease creation. Work limited to adding a READ-ONLY synthetic-test CI workflow on existing draft PR #209 and preparing a separate, draft-only F1 policy revision; inspecting only authorized ledgers for historical receipt evidence.

## BASELINE_PROVEN
Governance GitHub main manifest.version=f6fc9ca59a96e451; Windows preflight PASS job RET-CI-209-20261026. Existing previous v3 lease closed in finding 20261026-retention-v3-readonly-closure.md. Current draft PR #209 contains only two read-only modules, unit tests and docs. Existing GitLab mirror does not have the PR branch; do not mirror. F1 main version remains 2x remote copies, original local retained.

## FAILED_AVOIDED
Earlier rclone upload/copyto and Google Drive folder create were explicitly blocked by ChatGPT security controls. No retries or bypass. Production F1, credentials, queues, originals and publication remain unchanged.

## SUCCESS_SIGNAL
CI workflow runs ONLY synthetic test_retention_v3_readonly and Python syntax checking with read-only permissions; actual run/job success read back, not inferred. Receipt discovery reports path and schema with credentials redacted, with publication receipts explicitly separated from storage receipts. Separate F1 revision is draft-only with clear release gates and rollback.

## FAILURE_SIGNAL
Any attempt to publish, upload, move/delete Google Drive objects, delete media, change F1 runtime/cron, expose secrets or rewrite occupied paths. CI run blocked at provisioning is status NOT_TESTED, not PASS.

## TEST_VALIDITY
A Python CI green proves only the PR's synthetic QA tests, not real media provenance or 48-hour cleanup. No deletion code shall be introduced. Record verified IDs and current Git HEAD before subsequent changes.
