# AOI 16 — Lease para causa do erro de publicação Buffer
STATUS: RUNNING
AREA: cortes-instagram-buffer-error-cause
OWNER: ChatGPT AOI16
DATE_UTC: 2026-11-06
LEASE_MAX: 30 min from creation, auto-expires; branch-only.
BASE_MAIN_SHA: 23c01164ba02b510b8c35ad537a63f0f2936cbc6
GOVERNANCE_MANIFEST: 223433740e807a90
SCOPE: tools/cortes_buffer_instagram_cloud.py and .github/workflows/cortes-buffer-instagram-cloud.yml
GITHUB_SCRIPT_BLOB: a8a40b570105a3e840cfe95f5ecb759244b883ed
GITHUB_WORKFLOW_BLOB: b5d2d04336dcd91f99874b326e8ed4dce2c239c7
GITLAB_SCRIPT_BLOB: 12d647efa1685e62292339730c65c5e37ad9759a (divergent; no mirroring)
BASELINE_PROVEN:
- Run 42296479923 recorded Buffer status error for exactly three existing Instagram Buffer posts, 0 confirms, 0 new posts.
- Existing Buffer API post.error.message is documented by official GraphQL reference.
- Neon has 7 uncertain records, of which 3 have Buffer remote post IDs; no resubmissions authorized.
FAILED_AVOIDED: No new publication, readback repeated without diagnostic change, manual ledger updates, paid tiers, external PC runner.
SUCCESS_SIGNAL: classify official Buffer post.error.message safely and perform a single protected no-publish readback on a uniquely marked push; preserve all other workflow paths paused.
FAILURE_SIGNAL: overlapping owner lease, unexpected main/target blob, unauthorized workflow action or GraphQL schema error.
TEST_VALIDITY: isolated source checks only plus one real no-publish readback; no synthetic media.
ROLLBACK: revert PR through ordinary GitHub review.
COST_ADDED: R$0
