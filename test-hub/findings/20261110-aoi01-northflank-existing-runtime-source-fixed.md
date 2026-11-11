# AOI-01 — Northflank existing-runtime release gate, source repair
STATUS: SOURCE_FIXED_PENDING_MERGE
AREA: architecture/aoi01-northflank-existing-release
OWNER: chatgpt-aoi01-20261110-runtime-preflight
DATE_UTC: 2026-11-11
LEASE: CLOSED
SUPERSEDES: 20261110-aoi01-northflank-existing-runtime-lease.md
GITHUB_SOURCE_BASE: 4fb10c8da8bbb4756a767f12e33fb526d422844c
SOURCE_WORKFLOW_BLOB_BEFORE: 6ad878ee90227ef8081b82956cd7e3d1c1e813d8
SOURCE_WORKFLOW_BLOB_AFTER: 2eef24e5256a2b93f0e49a50e5a955a38941b21b
BRANCH: fix/aoi01-northflank-existing-runtime-20261110
GITLAB_PEER: 87307248 main remains independently divergent; not overwritten
TEST_COUNT: 5
TEST_MODE: local Python offline mocks, no network, no real secrets
TEST_RESULT: 5/5 PASS, py_compile PASS
TEST_CASES: deployed v12 with no admin token accepted (2 authenticated runtime checks, 0 admin requests); runtime401 fail closed (1 request); old version with no admin blocked (1 request); old version with admin401 blocked before build (2 requests); wrong browser backend blocked (2 requests).
PRODUCTION_DEPLOYED: false
PUBLISHERS_ENABLED: false
SOCIAL_PUBLICATIONS: 0
COST_ADDED: 0

## Change
- Northflank existing runtime is now checked first using the established runtime credential ARA_SHARED.
- Already-running v12 and good browser status can pass without the separate administrative API token.
- Stale version still requires real privileged Northflank API access before any build; unauthorized runtime 401/403 terminates before administrative calls.
- No Neon, TikTok identity, media publishing, Cloudflare secrets, Forgejo runners or session state changed.

## Scope and terminal acceptance
This closes the isolated source-code defect, not AOI-01. GitHub workflow is currently disabled_manually, so this edit is a reviewed draft PR. A fresh Northflank runtime v12 authenticated proof, TikTok account identity, Forgejo service recovery and real signed publication receipts remain pending. No remote privileged operation was attempted, and previous Hostinger-specific tool denial was preserved. 
