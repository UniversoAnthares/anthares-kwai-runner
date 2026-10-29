# AOI item fixo 4 — retirar checkout externo do CI Forgejo principal
STATUS: RUNNING
AREA: architecture/forgejo-main-ci-cd
DATE: 2026-10-29 UTC
RUN: none; source-only technical hardening
JOB: none
COMMIT: 65dfb087cbf56e3f336622d3d4d19caa4fdaaeb7
SUPERSEDES: 20261028-forgejo-principal-item4-lease.md (only checkout failure precondition)
LEASE: author ChatGPT AOI, scoped to .forgejo/workflows/anthares-main-ci-cd.yml and item4 finding; release after PR decision.
BASELINE_PROVEN: GitHub PR #1816 was merged to canonical main at 65dfb087cbf56e3f336622d3d4d19caa4fdaaeb7 as one manual-only workflow; 27 preexisting historical .forgejo workflows are fail-closed (item17 proof), sandbox runner ID 5 belongs exclusively to repo_id=20, no evidence of live main repo Actions or repo_id=1 runner. Prior AVS Forgejo Actions run #2 failed during external checkout, later offline mirror SHA contract run #3 succeeded (no publication).
FAILED_AVOIDED: no authenticated Forgejo query previously refused by security controls; no switch to another tool to reproduce refused operation; no Actions enable, runner registration, Windows staging or file writes, external publish, accounts or Neon changes.
SUCCESS_SIGNAL: source workflow has no remote checkout action, verifies exact repository/ref/SHA from existing Hostinger local Git mirror and runs the three offline quota cancellation contracts; CD writes only its private receipt after CI success. A single scoped static review verifies no auto trigger and no publishing.
FAILURE_SIGNAL: mirror lacks SHA or is stale, runner host doesn't expose mirror, Actions disabled, runner unavailable, forbidden administrative operation, unexpected nonlocal checkout.
TEST_VALIDITY: this change is static/source safety, NOT live CI/CD acceptance. Item #4 only closes after authorized repo Actions+runner and a terminal Forgejo CI/CD job with proof.
