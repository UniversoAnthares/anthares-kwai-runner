# AOI 16 — lease para correção de falsos alertas QA P0
STATUS: RUNNING
AREA: qa-p0-nonpublisher-false-alerts
DATE: 2026-11-04
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_EXPIRES: 2026-11-04T14:58:10.544Z
BASE_HEAD: 8aad3e7e90a0d39b61d58fa10cb49a6ef6000517
TARGET_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2015
TARGET_PR_HEAD: a15650af2ae9fab0cce69bf41c4c144d689ddf15
TARGET_BLOBS: tools/cortes_qa_p0_router.py aa6a02a3f1012529e8ee0b470d00186e6f255bf4; .github/workflows/cortes-qa-p0-publication-watchdog.yml 84414540b6b9322be6d868143331454056eb1fc9; tests/test_cortes_qa_p0_router.py 4cd6d924fd086cf6e2abdbc024b4af809c7ff00d
GOVERNANCE_MANIFEST: 223433740e807a90
RUN: none
JOB: none
SUPERSEDES: 20261031-qa-p0-nonpublisher-false-alerts-running.md

BASELINE_PROVEN: Cinco incidentes P0 espúrios são classificados como falhas de publicação por varreduras diagnósticas. PR #2015 filtra somente nomes de auditoria, preflight, watchdog e recuperação; testes dirigidos offline no finding 20261031-qa-p0-filter-targeted-execution-partial.md atestam 8/8 Python e 9/9 JS com publicadores reais preservados. GitHub e GitLab têm blobs idênticos dos dois filtros. Nenhuma mudança de schedule.
FAILED_AVOIDED: Não alterar PR original, não disparar Actions, não encerrar tickets P0, não publicar mídia nem operar PC. Não promover para DONE até execução externa e ausência de falso positivo verificadas.
SUCCESS_SIGNAL: patch de PR #2015 incorporado em main com HEAD e blob aprovados; regressão dirigida do filtro; recibo append-only e rollback por revert.
FAILURE_SIGNAL: conflito com trabalho de outro agente, exclusão de publisher real, quebra de CI, quota ou main SHA divergente.
TEST_VALIDITY: reutiliza QA offline já comprovada (mesmo código), verificação dirigida de diffs e readback GitHub; não repete testes de produção sem nova causa.
ROLLBACK: reverter somente filtro e testes após conferir SHA; preservar alertas reais e cron atual.
