# AOI #16 — lease: corrigir import do guard de retry de fontes longas
STATUS: RUNNING
AREA: cortes-general
DATE: 2026-11-09
OWNER: ChatGPT AOI — correção causal isolada do módulo qa/cortes_long_retry_guard.py em anthares-clipper
LEASE: scoped to source import of qa/cortes_long_retry_guard.py, no production activation
BASELINE_PROVEN: GitHub main 18aa437f90430a6c840444092e95b0d81ee7c1ae; blob 6de8487b45a48388875354a3a39235f3808fc317; GitLab peer main 20da3ac2ea3a3ef83ec8952e8cae0a5bf13a0de7, same source text; run 39881056747 job 120196022003 tests 3/3 PASS then ModuleNotFoundError: No module named 'cortes_source_adapter' from direct script invocation.
FAILED_AVOIDED: re-run of Windows self-hosted workflow; publishing media; retry of uncertain jobs; bypass of an explicitly denied operation.
SUCCESS_SIGNAL: direct entrypoint import resolves without touching production, focused regression passes, source PR with current base/lease and provider CI receipt.
FAILURE_SIGNAL: any import failure, changed main/peer conflict, lease collision, new Windows job or media side effect.
TEST_VALIDITY: isolated source regression and static command contracts; no production workflow dispatch.
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39881056747
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/jobs/120196022003
COMMIT: 18aa437f90430a6c840444092e95b0d81ee7c1ae
SUPERSEDES: none

No secrets, staging, new services or expenses. The AOI #16 remains PARTIAL until every distinct P0 passes its own terminal criteria.
