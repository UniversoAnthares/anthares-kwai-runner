# AOI item fixo 16 — impedir multiplicação de despachos QA P0 com fingerprint idêntico
STATUS: PARTIAL
AREA: architecture/qa-p0-incident-remediation
DATE: 2026-10-29 UTC
RUN: one offline JavaScript contract simulation (no external API calls)
JOB: none
COMMIT: 57957283d96c26b71446d1ce1fb9f4de53e62c27
SUPERSEDES: none
LEASE: scoped to .github/workflows/cortes-qa-p0-controller.yml and this finding; no exclusive claim on other P0 issues or publisher runners.

BASELINE_PROVEN: GitHub API read of open P0 issues 1871, 1872, 1873 (among 7 from 1867–1873) showed IDENTICAL marker QA-P0-FINGERPRINT:0e91ae0664e3b5bda5f57d47, network Threads and multiple source receipts. P0 controller formerly keyed cooldown only to GitHub issue number, not shared causal fingerprint, so each duplicate issue was separately eligible for executor dispatch.
IMPLEMENTED: only dispatch canonical lowest-number still-open P0 issue for each marker, whether scanning scheduled page list or handling issues events; fetch at most four pages of existing open labeled issues for incident-event admission, with early exit once older canonical match is found. Keep all original issues OPEN; no false issue closure, deduping publication content, re-publishing, ARA, Windows, Neon writes or quota increase.
TEST_VALIDITY: exact uploaded GitHub workflow JS extracted, parsed using JavaScript Function, then run in three no-network mocks using issue IDs 1871/1872/1873 sharing the real hash. Outcomes: issue 1871 leads to one simulated dispatch; 1872/1873 each lead to zero; all cases logged QA_P0_FINGERPRINT_DEDUP=PASS. No live issue dispatched by this test. Preserve controller's existing max-two-per-run and 3/6h attempt bounds.
LIMITS: the upstream external incident producer that CREATED seven duplicate GitHub issues remains unidentified. This change eliminates secondary duplicate executor consumption; actual Threads continuity failures and all other P0s remain unresolved and item 16 remains PARTIAL. No claims of remote publication repair.
FAILURE_SIGNAL: controller attempts to dispatch newer duplicate with same open fingerprint; canonical issue closed but newer issue suppressed; unavailable GitHub pagination or 403 must fail closed; duplicate publication attempt always prohibited without remote NOT_APPLIED and fencing.
NEXT_ACTION: verify one actual controller run after merge, reconcile source duplicate-issue writer and repair real Threads publication with receipts; do not repeatedly run full QA outside cadence.
