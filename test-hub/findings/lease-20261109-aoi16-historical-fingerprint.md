# AOI 16 — dedupe dos marcadores históricos QA-P0
STATUS: CLOSED
RESULT: PR #2243 merged, SHA 55c1d252844f9ac4f2b66b976413345451e4e853; exact historical fingerprint lookup added and 22 old duplicate GitHub QA-P0 issues closed in this operation. Canonical issues remain open, AOI #16 remains PARTIAL.
CLOSED_UTC: 2026-11-09T12:28:00Z
AREA: qa-p0-fingerprint-router
ITEMS: [16]
OWNER: chatgpt-aoi16-20261109-historical
BASE_HEAD: be52981c699387eefe4c16537351c8f3501e365e
START_UTC: 2026-11-09T11:51:00Z
EXPIRES_UTC: 2026-11-09T12:21:00Z
BASELINE_PROVEN: Router checks only five pages/500 GitHub issues; historical source #1556 fingerprint 81b0f6db9c83a2cc885af277 is found via live GitHub exact-text search in all-time issues (11 records), with 7 closed duplicate copies. Recreating this fingerprint wastes P0 capacity.
FAILED_AVOIDED: No publisher, queue, CI test dispatch, media or secrets. Current canonical issue remains open.
SUCCESS_SIGNAL: Earlier markers cause no new issue and fail closed on incomplete search with <=20 targeted searches/scan.
FAILURE_SIGNAL: GitHub search incomplete/denied or transient rate limit aborts safely, no duplicate issue created.
TEST_VALIDITY: Exact GitHub search readback + targeted mocked unit tests.
