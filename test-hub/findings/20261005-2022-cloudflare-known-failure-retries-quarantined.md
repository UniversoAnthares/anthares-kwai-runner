# Retries automáticos conhecidos foram colocados em quarentena
STATUS: PROVEN
AREA: github
DATE: 2026-10-05
RUN: none
JOB: workflow-policy
COMMIT: 6d4901ac8104422920ceb88b3dfcbcd6cb2e2f16
SUPERSEDES: none

## Objetivo
Parar a geração repetitiva de falhas conhecidas enquanto a credencial Cloudflare está ausente e produção está stale.

## Resultado
anthares-cloudflare-deploy-once.yml passou a workflow_dispatch apenas. anthares-cloud-failover.yml teve schedule removido temporariamente e foi alinhado a Render->GitHub->none, sem local e sem HLS WordPress hardcoded. cloud/anthares-failover.py não publica mais papéis local/kwai_web.

## Evidência decisiva
Commits 6352d0c3, a153f672 e 6d4901ac. Os últimos runs automáticos observados pertencem a commits anteriores às novas políticas; nenhum novo schedule deve ser criado por estes workflows até reativação deliberada após deploy.

## Consequência
Não reativar schedule/deploy automático antes de produção passar a versão v12. Depois do deploy, reativar somente o failover remoto, nunca fallback local.
