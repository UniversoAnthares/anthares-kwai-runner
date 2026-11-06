# AOI #16 — Threads continuity repeated-alert consolidation
STATUS: PARTIAL
ITEMS: [16]
AREA: qa-p0-threads-continuity-issue-dedupe
OWNER: chatgpt-aoi16-threads-issue-consolidation-20261106
DATE_UTC: 2026-11-06T18:32:23.488Z
EXPIRES_UTC: 2026-11-06T19:22:23.492Z
BASE_GITHUB_HEAD: 0cf1a256c3ed8111ebe1e50267704cdf35279065
GOVERNANCE_VERSION: 223433740e807a90
BASELINE_PROVEN: GitHub search of open `CONTINUITY_FAILURE` Threads QA-P0 found 94 entries, 32 distinct 24hex QA-P0 fingerprints, 18 fingerprints repeated (62 excess alerts). Each repeated group carries an identical source failure identity `fingerprint=YYYY-MM-DD:threads:CONTINUITY_FAILURE:<hash>` and distinct original evidence filenames. Earlier upstream throttle & controller dedupe corrections are documented in 20261029-item16-threads-same-fingerprint-12h-source-fix.md and 20261029-item16-qa-p0-fingerprint-dispatch-dedupe-partial.md.
FAILED_AVOIDED: no media upload, publisher reactivation, ledger rewrite, background job, source telemetry deletion or false incident resolution. Historical multiple evidence receipts must be retained in canonical issue.
SUCCESS_SIGNAL: per fingerprint keep smallest-number original as OPEN; add canonical evidence manifest with every related issue and evidence filename; annotate & close only proven same-cause duplicates with GitHub state_reason=duplicate; preserve comments/fingerprint and QA-P0 classification; report exact succeeded count.
FAILURE_SIGNAL: issue/canonical state changed, fingerprint/identity mismatch, security denial, Github quota error, competing lease or mutable issue unexpected edit; stop without rerouting denied operations.
TEST_VALIDITY: real GitHub issue readback and issue state receipts only; no synthetic publishing QA and no additional tests.
PEER: GitLab project 87307248 path of new finding absent (HTTP404), no mirror write or cross-provider reconciliation.
COST_ADDED: R$0
ROLLBACK: reopen individual issue with explicit rationale; original evidence remains unchanged.

## Resultado terminal da rodada
STATUS_FINAL: PARTIAL
LEASE: CLOSED
CLOSED_DUPLICATE_REAL_RECEIPTS: 53
CANONICAL_GROUPS_TOUCHED: 13
CANONICAL_GROUPS_FULLY_CONSOLIDATED: 12
BASELINE_DISTINCT_THREADS_CAUSES: 32
ORIGINAL_OPEN_CONTINUITY_ISSUES: 94
EXPECTED_REMAINING_OPEN_AFTER_THIS_ROUND: 41
PENDING_EXCESS_DUPLICATES: 9
DENIED_PENDING_REVIEW: issue #1423 — `update_issue` refused explicitly by OpenAI security. No repeat and no alternate write channel. The separate issue #1425 and older groups stay open pending normal allowed review.

### Causas e recibos reais
- Canonical #1857 remains OPEN; 6 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1867 remains OPEN; 6 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1946 remains OPEN; 7 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1768 remains OPEN; 2 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1754 remains OPEN; 3 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1755 remains OPEN; 3 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1764 remains OPEN; 3 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1483 remains OPEN; 6 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1349 remains OPEN; 5 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1180 remains OPEN; 5 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1192 remains OPEN; 3 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1278 remains OPEN; 3 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.
- Canonical #1419 remains OPEN; 1 alias issues closed by GitHub `state_reason=duplicate`; canonical issue comment lists every preserved original evidence file and the causal fingerprint.

Fully consolidated roots: #1857, #1867, #1946, #1768, #1754, #1755, #1764, #1483, #1349, #1180, #1192, #1278. Root #1419 partial: only #1421 closed; #1423 write DENIED_PENDING_REVIEW; #1425 left open.

Unattempted residual groups: #1189 (1), #1281 (1), #1420 (3), #1429 (1), #1492 (1), plus #1425 (1) and denied #1423 (1). No incident in this list is declared operationally resolved.

### QA and safety outcome
- Every closed alias had current `open` state, matching full 24-character marker, matching source causal identity, and original body readback. The `update_issue` success receipt returned `state=closed`, `state_reason=duplicate`; issue body preserved forensic evidence with canonical link.
- Initial affected independent namespace: `qa-p0-threads-continuity-issue-dedupe` only. Previous #2047 publication/workflow security refusal remains untouched.
- Existing upstream 12h Threads alert throttle and fingerprint-based GitHub QA executor dispatch protection were retained. Real Threads public posting remains unverified and active canonical P0s remain OPEN.
- LinkedIn personal new uncertain receipt and Instagram/CORTES P0s were not changed; publication jobs did not run in this action.
- No additional quota, billing, runners, secrets, PC jobs, media uploads, or production scheduler modification. No tests needed for issue-only identity deduplication.
- Rollback is per closed alias with explicit rationale and preserved original content; this finding is evidence, not authority to bypass the security refusal.
