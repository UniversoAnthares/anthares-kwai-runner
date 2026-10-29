# Item fixo 4 — CI/CD não publicador do Forgejo principal, código pronto e admissão pendente
STATUS: PARTIAL
AREA: architecture/forgejo-main-ci-cd
DATE: 2026-10-29 UTC
RUN: none (repo principal Forgejo real run unproven)
JOB: none
COMMIT: bfc2b66ab34dc4a8dca29a9e8a51c820fcf1279d
SUPERSEDES: 20261028-forgejo-principal-item4-lease.md, 20261029-item4-main-ci-offline-checkout-running.md
LEASE: CLOSED for GitHub source updates. Administrative Forgejo enablement remains separately gated.

BASELINE_PROVEN: Existing nonpublisher Forgejo sandbox runner ID5, scoped only to repo_id20, completed seven CI workflows. Item17 quarantined 27 historical workflows with 28 job-level false gates. Before this round, Forgejo main repo_id1 Actions was read as disabled and no main runner was registered, although current administrator-side state could not be rechecked.
FAILED_AVOIDED: no repetition of an authenticated Forgejo query previously refused by security controls; no Forgejo administrative change via another channel; no Windows work, no runner relocation across repository scope, no media, Neon writes, quota increase, paid service or social promotion.
IMPLEMENTED: GitHub PR #1816 is merged at 65dfb087cbf56e3f336622d3d4d19caa4fdaaeb7: new `.forgejo/workflows/anthares-main-ci-cd.yml` with `workflow_dispatch` only, branch/repo scope checks and dedicated runner label `anthares-ci-main-host`. PR #1854 is merged at bfc2b66ab34dc4a8dca29a9e8a51c820fcf1279d: removed two external `actions/checkout@v4` dependencies, replaced with local Hostinger mirror `git archive` at exact `FORGEJO_SHA` and limited test-file readback; CD only writes/reads its private Hostinger receipt after successful CI.
SOURCE_READBACK: canonical GitHub main SHA bfc2b66ab34dc4a8dca29a9e8a51c820fcf1279d; new workflow blob 9cb5859f8331c17bfe06ace98abfa835ff8e49b0; source checks: 1 manual trigger, 2 repo-scope jobs on dedicated label, 0 external checkout actions, no publication paths.
SUCCESS_SIGNAL_PUBLISHED_SOURCE: manual-only scoped workflow and offline SHA-checked checkout integrated and read back in canonical GitHub. Neither a GitHub merge nor a sandbox runner success proves Forgejo repo principal CI/CD execution.
FAILURE_SIGNAL: Forgejo Actions disabled/no unit 10; no repo_id1 runner; missing Hostinger mirror SHA; CI or CD failure; no terminal Forgejo run/job or receipt.
NEXT_ESSENTIAL_GATES: (1) legitimate administrator enables Actions at `anthares-admin/anthares-kwai-runner` after confirming legacy workflow quarantine; (2) a dedicated existing Hostinger-compute runner registers with repository scope, label `anthares-ci-main-host`, persistent supervised identity and no publisher secrets; (3) admin authorizes one manual `anthares-main-ci-cd.yml` dispatch at main after verified Forgejo mirror parity; (4) independent real Forgejo job and CD receipt prove SHA and PASS. Then item4 may become DONE.
TEST_VALIDITY: static source review of manual-only trigger, explicit SHA checks, exact checkout subset and log success markers. No live Forgejo run, runner deployment, actions activation or production deployment.
COST: no extra plan/quota; no new provider. ROLLBACK: revert source commits if necessary, preserve historical quarantines.
