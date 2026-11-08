# AOI #16 — Duplicatas de masters 22/10
STATUS: PROVEN
AREA: qa-p0-daily-masters-20261022-duplicate-issues
DATE_UTC: 2026-11-08T23:19:21.064Z
LEASE_EXPIRES_UTC: 2026-11-08T23:54:21.068Z
OWNER: chatgpt-aoi16-daily-masters-dedupe-20261108
ITEMS: [16]
BASE_GITHUB_HEAD: c5fbda6b12c6d51d3dd52e60dc60e96ef40d4db3
GOVERNANCE_VERSION: 223433740e807a90
PEER_CHECK: GitLab project 87307248 main new finding absent (404). No GitLab writes.
BASELINE_PROVEN: #610, #774 and #955 OPEN with identical QA-P0-FINGERPRINT:4cedac2ab0541ae121604f2c, same stage P0_DAILY_PRODUCER_ZERO_MASTERS, same date 22/10 and identical description of zero masters after 07:00 local. #610 is canonical. #1060 has different Kwai enqueue description, excluded.
FAILED_AVOIDED: No media, reenqueues, publication, dispatch, secrets, Neon or runtime changes. Preserve #610 OPEN.
SUCCESS_SIGNAL: #774 and #955 closed as duplicate of #610 with original body preserved; #610 remains open; confirm readback.
FAILURE_SIGNAL: changed source, conflict, security denial or distinct evidence; stop without fallback evasivo.
TEST_VALIDITY: Real GitHub issues readback and exact fingerprints, no media tests.
COST_ADDED: 0
ROLLBACK: reopen duplicate issues when justified; original bodies remain unchanged.

## Resultado
LEASE: CLOSED
LEASE_CLOSED_UTC: 2026-11-08T23:20:23.318Z
CLOSED_DUPLICATES: #774 #955, GitHub state_reason=duplicate, bodies preserved.
CANONICAL_OPEN: #610 remains open (root producer incident unresolved).
DISTINCT_NOT_TOUCHED: #1060 (Kwai enqueue distinct description).
ITEM_16_FINAL: PARTIAL; closing duplicates is not evidence of producer repair.
EVIDENCE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/610 ; https://github.com/UniversoAnthares/anthares-kwai-runner/issues/774 ; https://github.com/UniversoAnthares/anthares-kwai-runner/issues/955
COST_ADDED: 0; MEDIA_POSTED: 0; WORKFLOWS_DISPATCHED: 0
