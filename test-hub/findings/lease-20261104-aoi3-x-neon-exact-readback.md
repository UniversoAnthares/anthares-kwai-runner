# AOI #3 — X ledger immutable readback lease
STATUS: RUNNING
DATE_UTC: 2026-11-04T21:25:50.692Z
EXPIRES_UTC: 2026-11-04T21:55:50.692Z
OWNER: chatgpt-aoi3-20261104
AREA: architecture/x-neon-ledger-historical-readback
ITEMS: [3]
BASE_HEAD: 52030b11b35dbbce48b3cc48734305d94d719694
SCOPE: find-only evidence in Test Hub, no publishers/queues/credentials/Neon writes.
BASELINE_PROVEN: 12 X-PUBLISH issues discovered (2 fixtures, 10 eligible long), Neon has 9 confirmed rows. Nine hashes independently rederived from the issue payloads match full Neon identifiers.
FAILED_AVOIDED: no old Northflank ledger mutation, no X post, no claim/retry of issue1002, no migration_verified flag, no live CI cost.
SUCCESS_SIGNAL: durable record of 9 exact confirmed matches and one missing with source-of-truth caveat.
FAILURE_SIGNAL: promoting old issue1002 or publisher without authoritative old status proof.
TEST_VALIDITY: read-only GitHub issue bodies and Neon LEFT JOIN; no tests of remote social publication.
