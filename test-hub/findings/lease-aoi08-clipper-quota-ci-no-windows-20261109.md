# AOI #08/#18 — corrigir CI estático de política de cotas sem Windows
STATUS: RUNNING
AREA: quota-ci-static
DATE_UTC: 2026-11-09
ITEMS: [8,18]
OWNER: chatgpt-aoi08-clipper-quota-ci-20261109
LEASE_SCOPE: exclusively UniversoAnthares/anthares-clipper/.github/workflows/cortes-quota-policy.yml
LEASE_EXPIRES_UTC: 2026-11-09T02:38:00Z
BASE_CLIPPER_HEAD: d5e830222691e106dda64e481023fb5c34bedb05
BASE_WORKFLOW_SHA: 5a3d7680ead516aa14c6533f9aeca82c746253f1
GOVERNANCE_VERSION: 223433740e807a90
PREVIOUS_RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40493364103
BASELINE_PROVEN: Workflow requires [self-hosted, Windows] and fixed Python path on owner's PC for unit/static tests. Historical failed run is terminal; expired logs do not establish its exact error. Hosted Linux CI already runs other Clipper jobs.
FAILED_AVOIDED: no PC runner, no Windows artifacts, no live queue, no media, no quota exhaustion test, no publication, no new paid service.
SUCCESS_SIGNAL: code change limited to static CI executor; all existing tests retained and passed on approved hosted CI within free available quota.
FAILURE_SIGNAL: repository/runner quota insufficient, tests fail, stale base, conflicting lease, policy refusal.
TEST_VALIDITY: syntax and unit tests only; GH Actions success is not a real provider failover or posting proof.
ROLLBACK: revert workflow-only change. Existing publication code unchanged.
