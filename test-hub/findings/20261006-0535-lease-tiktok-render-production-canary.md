# Lease: TikTok production canary via proven Render browser path
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
LEASE_AREA: tiktok-publish
LEASE_EXPIRES: 2026-10-06T06:05:00Z
BASELINE_PROVEN: Cloudflare OIDC blocker closed by run 37418647980; central session remains valid and Render path has identity_verified=true/upload_page_auth=true; 15-way GitHub browser matrix proved GitHub auth is environment-dependent.
FAILED_AVOIDED: do not use GitHub-hosted browser as the irreversible publisher; do not reuse exhausted/stale queue identities; do not weaken queue fencing, publication_started, independent confirmation or ledger gates.
SUCCESS_SIGNAL: TIKTOK_CANARY_PRODUCTION_PROVEN with nonempty remote_id, independent post verification and central status=published confirmed=true.
FAILURE_SIGNAL: any pre-publication readiness gate fails; after publication_started any ambiguous failure must become UNCERTAIN.
TEST_VALIDITY: one fresh canary identity; Render exact-account readiness immediately before started; deterministic owned MP4; no second irreversible attempt.
