# AOI #16 — LinkedIn personal preupload media failure classification
STATUS: RUNNING
ITEMS: [16]
AREA: qa-p0-linkedin-personal-media-preflight
DATE_UTC: 2026-11-06T02:36:13.318Z
EXPIRES_UTC: 2026-11-06T03:21:13.321Z
OWNER: chatgpt-aoi16-linkedin-media-20261106
BASE_HEAD: 8475395b719042cece4490f10956aef1ff6aee54
GOVERNANCE_MANIFEST: 223433740e807a90
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41260916613
JOB: 124713825853
ISSUE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/2043
BASELINE_PROVEN: historical hosted log reaches PERSONAL_STAGE=media_readonly after account preflight and queue lease, then RuntimeError and generic BLOCKED_OR_UNCERTAIN with no upload-stage marker. Neon read has 115 confirmed and 4 uncertain personal rows; these are independent historical states, not evidence to replay. Current personalAction 'fail' returns leased status to queued if publication_started_at IS NULL, and fences by id, owner and generation.
CAUSE_SCOPE: preupload media probe raises bounded SOURCE_MEDIA_* RuntimeError codes, currently hidden behind generic exception type. Specific source or remote transport incident behind the historical runtime error is UNVERIFIED; avoid claiming proven 404/timeout.
PEER_READBACK: GitLab 87307248 main files tools/cortes_linkedin_personal_cloud.py SHA 1243f006293925af4cebdd185f8b5a3bdcdef859 and tests/test_cortes_linkedin_personal_cloud_continuity.py SHA db45baba75efeb79217e79f63011e2f2c7532b5d match current GitHub main.
FAILED_AVOIDED: no social post, workflow reactivation, duplicate job, status rewrite or unsafe reclaim of uncertain row; no user PC runner, new costs, credentials or new third-party service.
SUCCESS_SIGNAL: exact bounded known SOURCE_MEDIA_* preupload exception, only after successful fenced queue('fail') completion, becomes sanitized BLOCKED_BEFORE_UPLOAD with nonzero exit; no queue start/upload and a regression assertion passes. If queue fail cannot be acknowledged, preserve existing generic BLOCKED_OR_UNCERTAIN.
FAILURE_SIGNAL: another writer changes branch, queue control regression, exception misclassification, auth/security denial, or unsupported tests.
TEST_VALIDITY: isolated regression with stubbed media/queue/LinkedIn and no network; code proof only, not end-to-end publisher or global AOI item DONE.
SCOPE: tools/cortes_linkedin_personal_cloud.py and tests/test_cortes_linkedin_personal_cloud_continuity.py, append-only Test Hub finding.
ROLLBACK: revert PR; disabled production workflow stays disabled.
COST_ADDED: R$0
