# CI-01 SHADOW-01 — gatilho automático main comprovado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-25
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40203503483
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40203503483/job/121199456379
COMMIT: db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none
RELATES_TO: test-hub/findings/20261025-ci01-shadow-readonly-ci-proven.md

## Objetivo
Comprovar que o workflow SHADOW-01 recém-integrado dispara automaticamente em push para main com escopo de 27 testes sintéticos e produz evidência durável.

## Resultado e evidência
Evento push no commit db6c12fdaa0af01e3b68b8a527b2e02c12c21837 disparou run 40203503483, job 121199456379; status completed/success. Todas as etapas, inclusive upload do artefato, terminaram success. Log registra 'Ran 27 tests in 0.259s', 'OK' e 'SHADOW01_QA_CASES=27'. Artifact ID 12602528476; SHA-256 ZIP 618fa7ef34f15154e5ffa805a9f5ef8fc37fd68e814377e22bf05dba7bcbc441.
A configuração de gatilhos PR/push é filtrada por código de auditor shadow e seu workflow, com contents:read e timeout de 4 minutos. Nenhuma ação de deploy, SQL, alteração de fila ou publicação.

## Limites
Este finding complementa o finding PROVEN anterior. CI-01/SHADOW-01 (gating regressões sintéticas) está concluído. O CI-01 global dos outros contratos e a prova de runner cloud permanecem parciais. Execução Windows self-hosted, preservadas as quatro suítes restritas e a necessidade de IAM/RLS/ACL e single writer real.
