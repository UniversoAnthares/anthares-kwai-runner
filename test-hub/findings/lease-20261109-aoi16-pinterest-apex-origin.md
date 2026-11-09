# AOI #16 — Pinterest PIN_WRONG_ORIGIN apex gate
STATUS: RUNNING
AREA: pinterest-browser-origin
DATE: 2026-11-09 UTC
ITEMS: [16]
OWNER: chatgpt-aoi16-pinterest-apex-20261109
SOURCE_ISSUES: #1978, #1981
BASE_HEAD: 8efc7079c4f7a5ec14fdfce0c60d74669c842006
TARGET_BLOB: 2b517f082ed71404200e036ffc3334d630cb8b2b
PEER: GitLab 87307248 main same byte content
LEASE_SCOPE: tools/cortes_pinterest_browser_ui.mjs origin host predicate only
BASELINE_PROVEN: page(url) accepts https://pinterest.com/pin-creation-tool/; session(p) rejected apex host because it only accepted .pinterest.com suffix.
FAILED_AVOIDED: changing account, login, publishing gates, local runner, credentials, or media; no test publication.
SUCCESS_SIGNAL: source accepts exact pinterest.com and valid subdomains and rejects lookalikes; JS syntax and directed assertion PASS.
FAILURE_SIGNAL: scope drift, concurrent target update, invalid syntax or unexpected origin accepted.
TEST_VALIDITY: static only, no browser or upload. P0 overall remains open until legitimately authorized remote production proof.
