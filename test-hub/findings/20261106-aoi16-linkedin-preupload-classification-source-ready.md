# AOI #16 — LinkedIn personal media preupload failure classified safely
STATUS: PARTIAL
ITEMS: [16]
AREA: qa-p0-linkedin-personal-media-preflight
DATE_UTC: 2026-11-06T02:42:20.171Z
OWNER: chatgpt-aoi16-linkedin-media-20261106
LEASE: CLOSED
SUPERSEDES: 20261106-lease-aoi16-linkedin-personal-media-preflight.md
SOURCE_COMMIT: 83ee9990a903166acb4f362c0b94c3af83398046
TEST_COMMIT: 6727e12393c666116d88204d56f36f133b393876
INCIDENT: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/2043
RUN_EVIDENCE: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41260916613
JOB_EVIDENCE: 124713825853
GOVERNANCE_VERSION: 223433740e807a90
PEER_BASELINE_BLOBS: 1243f006293925af4cebdd185f8b5a3bdcdef859; db45baba75efeb79217e79f63011e2f2c7532b5d
COST_ADDED: R$0
PRODUCTION_UPLOADS: 0

## Diagnóstico existente
Real GitHub log reached PERSONAL_STAGE=media_readonly after identity, lease and LinkedIn readiness, then RuntimeError/BLOCKED_OR_UNCERTAIN without any queue_start or linkedin_upload marker. The exact subtype of RuntimeError was not exposed by the historic job, so this does not establish HTTP, timeout or a definitive source-media root cause. The live Neon ledger contained 115 confirmed and 4 uncertain linkedin:personal rows; they are preserved.

## Código e prova dirigida
Only the preupload exception handler was changed in tools/cortes_linkedin_personal_cloud.py. Five allowlisted SOURCE_MEDIA_* RuntimeError codes are reported as BLOCKED_BEFORE_UPLOAD solely after an acknowledged fenced personal-fail call. Unconfirmed release, unexpected failure or an exception after queue_start keeps the old uncertain/failed handling. Existing publisher authorization, upload, remote receipt, daily limit and queue idempotency logic stay intact.
Two regression cases were added to tests/test_cortes_linkedin_personal_cloud_continuity.py. An isolated Python compile and directed 2-case execution of the exact edited publish_one and main function bodies with stubbed account, queue, LinkedIn and media operations both passed: acknowledged release -> exit 2 BLOCKED_BEFORE_UPLOAD; unconfirmed release -> exit 3 BLOCKED_OR_UNCERTAIN; each had no start/upload action.
Full repository unittest and GitHub PR CI have not executed: the isolated environment's GitHub hostname resolution failed and the PR commit had zero Actions runs and statuses on initial readback. The tests are versioned for normal eligible CI; this finding attests bounded source/branch safety, not production runtime qualification.

## Completion boundary
Subtype distinction and local safety path are SOURCE_READY for AOI #16. Original QA issue #2043 remains open; no publisher was reactivated, no uncertain posts retried, and no remote publication evidence fabricated. AOI fixed item #16 remains PARTIAL until actual P0 closures with remote receipts. No payment or new provider.
ROLLBACK: revert the source PR and retain existing older queue behavior. Lease ended.
