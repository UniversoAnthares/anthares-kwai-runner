# AOI #16 — Threads continuity repeated-alert consolidation
STATUS: RUNNING
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
