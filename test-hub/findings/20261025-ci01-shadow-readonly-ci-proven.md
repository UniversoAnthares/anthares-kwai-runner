# CORTES CI-01 / SHADOW-01 — regression CI real (scoped)
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-25
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40203398441
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40203398441/job/121199145269
COMMIT: db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: test-hub/findings/20261025-ci01-shadow-hosted-running.md
LEASE_AREA: cortes-shadow01-hosted-ci
LEASE_STATUS: CLOSED

## Objetivo
Automatizar os 27 testes já versionados do auditor SHADOW-01, com gatilho estreito por arquivo em PR e push, sem segredos ou publicação e com recibo verificável. Manter workflow geral de regressões manuais inalterado.

## BASELINE_PROVEN
SHADOW-01 já possuía 27/27 testes Python aprovados em Windows isolado (finding 20261025-cortes-shadow01-persistent-regressions.md).

## FAILED_AVOIDED
Primeira execução hospedada run 40203247786 concluiu failure antes de qualquer step, runner=null, sem log ou artifact: falha pré-execução, classe NOT_TESTED (não regressão de código). Por isso, a revisão da PR #203 trocou somente o job de QA para o runner Windows self-hosted existente, preservando o mesmo escopo e sem usar suites anteriormente restritas, secrets, banco, perfis ou produção.

## SUCCESS_SIGNAL
PR https://github.com/UniversoAnthares/anthares-clipper/pull/203 integrada no main, squash commit db6c12fdaa0af01e3b68b8a527b2e02c12c21837; readback confirmou .github/workflows/cortes-shadow01-readonly-qa.yml (blob 6b4ebefba068a462a235d068f696847ec7540cf8).
GitHub Actions run 40203398441 job 121199145269 STATUS completed/success, checkout, Python e execução dos testes aprovados; log contém 'Ran 27 tests in 0.239s', 'OK', 'SHADOW01_QA_CASES=27', 'SHADOW01_CUTOVER_AUTHORIZED=0', 'SHADOW01_PUBLISHER_INVOKED=0'.
Upload de artefato concluído em step SUCCESS: artifact ID 12602224008, 769 bytes ZIP, SHA-256 288edd528c6e0a8e1d4b8b6579b82feaaf6fb046dcc0bfb7a49a3d6295a1badc, https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40203398441/artifacts/12602224008 .

## TEST_VALIDITY
PROVEN apenas CI automático de testes sintéticos do auditor shadow. Não certifica deploy, publicação, segregação real IAM/ACL/RLS, single writer, nem controle CI total do CORTES. Os 15 testes de suites gerais continuam no workflow manual separado; quatro suítes com restrição explícita continuam excluídas. O runner Windows self-hosted está apto neste teste, mas a capacidade cloud hospedada continua lacuna, pois falhou antes de alocação. Sem autorização de gastos ou novas credenciais.

## Consequência
Subitem CI-01/SHADOW-01 (QA automático de regressão) CONCLUÍDO e integrado no main. O controle global CI-01 dos workflows de isolamento permanece PARCIAL até homologação dos gates mais abrangentes e runner cloud elegível; nenhum recurso de publicação foi ativado. Lease CLOSED. 
