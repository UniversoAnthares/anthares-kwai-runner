# AOI #16 — classificação de visibilidade GitHub
STATUS: RUNNING
AREA: qa-p0-visibility-classification
LEASE_OWNER: chatgpt-optimization-20261104
LEASE_EXPIRES: 2026-11-04T18:02:30.806Z
BASE_HEAD: 11a1703c037b69afc78308ad70f8bcfd7f06330d
BASE_BLOB_ROUTER: 3c0f0e146eb02787d415155bddf968a0d04f093d
BASE_BLOB_TEST: 5becb656c040fb1d6fbb53d4de78594cb160ade2
ITEMS: [16]
GOVERNANCE_MANIFEST: 223433740e807a90
RELATED_PR: #547 OPEN, same files but hunks unrelated; do not change PR branch
RUN: none
JOB: none
COST_ADDED: 0
BASELINE_PROVEN: issues #2045/#2028 have stage qa_visibility_lost_github_repo but title and publication-failure label incorrect. GitHub private actions read failure does not itself prove media publication failed.
FAILED_AVOIDED: no issue closure before causal proof, no publisher activation, no remote_exec retry (security denied), no new workflow or scheduler.
SUCCESS_SIGNAL: visibility-only issue is QA-P0 infra with diagnostic action, real publishing issues preserve title, label, retry/uncertain safeguards; regression tests verified.
TEST_VALIDITY: isolated local static checks and canonical readback, no CI or posts.
ROLLBACK: revert narrow PR, preserve all original issue records.