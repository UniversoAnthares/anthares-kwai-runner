# Lease: TikTok final production E2E
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
LEASE_AREA: tiktok-publish
LEASE_EXPIRES: 2026-10-06T11:47:00Z
BASELINE_PROVEN: control/fencing/dedupe/reconciliation are PROVEN; central session is valid; Render identity/upload auth is PROVEN; v13 OOM at 512Mi was safely reconciled absent; current v14 changes the mechanism to a materially lower-memory /publish-lean path and one tiny owned canary.
FAILED_AVOIDED: do not retry v13 unchanged; do not run duplicate irreversible attempts; do not use GitHub browser contenders unchanged; after publication_started, any ambiguity stays UNCERTAIN until independent profile reconciliation.
SUCCESS_SIGNAL: TIKTOK_REAL_REMOTE_POST=PROVEN with nonempty remote_id, independent profile evidence, and central job status published confirmed=true.
FAILURE_SIGNAL: v14 low-memory publisher still OOMs/fails or independent profile inventory cannot confirm the post; in that case create a materially different free execution mechanism before another attempt.
TEST_VALIDITY: exact fresh v14 identity, fenced lease, publication_started before publish, one tiny owned MP4, independent profile inventory, no second irreversible attempt without reconciliation.

Objective: close the only remaining TikTok acceptance gate without PC runtime dependency.