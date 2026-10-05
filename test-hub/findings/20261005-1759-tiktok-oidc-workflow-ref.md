# Validador OIDC usava claim inadequada para workflow direto
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378729369
JOB: 111994756820
COMMIT: ab3565d8957b01f180dd420a0c218a23f227d411
SUPERSEDES: test-hub/findings/20261005-1755-tiktok-oidc-allowlist.md

## Objetivo
Encontrar por que a autorização do repositório público continuava 401 mesmo após ampliar a allowlist.

## Resultado
O validador Render lia job_workflow_ref. A documentação do GitHub define job_workflow_ref para jobs que usam reusable workflows; workflow_ref identifica o workflow normal que está executando. O código foi alterado para usar workflow_ref com fallback para job_workflow_ref e um novo deploy Render foi disparado.

## Evidência decisiva
O run 37378729369 continuou 401 após a revisão anterior estar live. Revisão do código mostrou dependência de job_workflow_ref. Documentação oficial do GitHub diferencia workflow_ref de job_workflow_ref. Commit corretivo ab3565d8957b01f180dd420a0c218a23f227d411; deploy Render dep-db21rd2jnfac73ejbf6g iniciado.

## Consequência
Não repetir validação de workflows diretos baseada somente em job_workflow_ref. Após o novo deploy ficar live, executar primeiro uma prova OIDC mínima; somente se passar executar sessão, identidade e dry-runs.
