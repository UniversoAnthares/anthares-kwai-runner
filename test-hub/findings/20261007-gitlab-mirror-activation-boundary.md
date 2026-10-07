# GitLab mirror activation boundary

STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: none
COMMIT: 1d1a7fc8211b4dfdfd99628d1ace03d564358ff2
SUPERSEDES: none

## Objetivo
Deixar o transporte GitHub → GitLab preparado sem armazenar credenciais no repositório.

## Resultado
O workflow foi restaurado em uma branch dedicada e submetido em PR #8. A ativação autenticada continua deliberadamente condicionada ao secret `GITLAB_MIRROR_URL`.

## Evidência decisiva
O workflow valida `GITLAB_MIRROR_URL` antes de qualquer push e compara o SHA de `main` entre os provedores após o push.

## Consequência
Nenhum agente deve gravar token/PAT/Deploy Token no repositório ou no Test Hub. A etapa restante é provisionar o secret fora do conteúdo versionado.
