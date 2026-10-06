# Lease: TikTok GitHub 30-way authenticated contender
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
LEASE_AREA: tiktok-publish
LEASE_EXPIRES: 2026-10-06T06:30:00Z
BASELINE_PROVEN: v13 Render attempt reached publication_started then Render was OOM-killed at 512Mi; independent profile inventory found zero posts and v13 was reconciled confirmed_absent to queued. Fifteen serialized GitHub contenders produced no authenticated /upload in the latest round, while an earlier 15-way matrix proved at least one environment can authenticate.
FAILED_AVOIDED: do not retry Render 512Mi publication; do not publish without exact v13 queue lease; do not retry after any publication_started ambiguity without reconciliation.
SUCCESS_SIGNAL: TIKTOK_REAL_REMOTE_POST=PROVEN with profile-derived remote_id and central confirmed published ledger.
FAILURE_SIGNAL: all 30 contenders unauthenticated, or the sole lease winner fails after publication_started and becomes UNCERTAIN.
TEST_VALIDITY: central v13 is queued only after independent confirmed-absent reconciliation; contenders use identical central session; queue exact lease serializes the irreversible action.
