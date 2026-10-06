# TikTok canary v4 — fresh queue identity after v3 exhausted attempts
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
BASELINE_PROVEN: authorized central-session rehydrate run 37412149475 proved 21-cookie central state, Render bootstrap, identity_verified=true, dry-run readiness, and persistence. V3 run 37412477890 failed before publication_started.
FAILED_AVOIDED: do not reuse v3 job/dedupe identity. V3 is queued with attempts=5; queue lease intentionally selects attempts<5, so re-enqueue deduplicates to an unleaseable exhausted job. Do not alter the proven MAX_ATTEMPTS queue invariant.
SUCCESS_SIGNAL: TIKTOK_CANARY_PRODUCTION_PROVEN with remote_id, independently verified new post, and central job status=published confirmed=true.
FAILURE_SIGNAL: any pre-publication gate fails; or after publication_started the workflow must fail closed to UNCERTAIN until independent reconciliation.
TEST_VALIDITY: use a fresh v4 job/dedupe/source identity only because v3 publication_started=false. Preserve deterministic owned MP4, immediate identity verification, fencing, started-before-publish, independent confirmation and ledger complete requirements.

## Causal hypothesis
A fresh queue identity removes the exhausted-attempts condition while preserving all production safety gates.