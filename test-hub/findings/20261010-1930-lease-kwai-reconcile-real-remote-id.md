# Lease: fail-closed Kwai reconciliation requires real remote post identity
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-10
OWNER: chatgpt-kwai-safety-1930Z
LEASE_UNTIL: 2026-10-10T19:45:00Z
BASELINE_PROVEN: Cloudflare v16 queue fencing active, publisher paused pending credential rotation, publisher run 38079188085 stopped at AUTH_REQUIRED without claiming queue; prior evidence confirms real post URL/ID has never been observed.
FAILED_AVOIDED: never create a fake remote post ID from queue job ID; do not retry irreversible publish or bypass identity; no credentials used in QA.
SUCCESS_SIGNAL: reconciliation request requires an independently observed KWAI_REMOTE_POST_ID, never constructs `kwai:<queue_job_id>`; static test and CI pass.
FAILURE_SIGNAL: a caller can still reconcile using fabricated queue-job ID or without remote post identity.
TEST_VALIDITY: unit/static check only, no claim of real publication. No changes to Cloudflare production.
