# GitLab mirror activation boundary

STATUS: PROVEN
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: none
COMMIT: 3eb88be28a29f3653d1e458390532dfab971cde7
SUPERSEDES: none

## Objetivo
Deixar o transporte GitHub → GitLab preparado sem armazenar credenciais no repositório.

## Resultado
O workflow foi restaurado em uma branch dedicada, submetido no PR #8 e mesclado em `main`. A ativação autenticada continua deliberadamente condicionada ao secret `GITLAB_MIRROR_URL`.

## Evidência decisiva
O workflow valida `GITLAB_MIRROR_URL` antes de qualquer push e compara o SHA de `main` entre os provedores após o push.

## Consequência
Nenhum agente deve gravar token/PAT/Deploy Token no repositório ou no Test Hub. A etapa restante é provisionar o secret fora do conteúdo versionado.
