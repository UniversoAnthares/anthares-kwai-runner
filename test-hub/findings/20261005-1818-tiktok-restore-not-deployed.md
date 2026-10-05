# Restore central ainda não havia sido implantado
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: none
JOB: Render deploy dep-db224ee7bikc73c5npe0
COMMIT: cdd656b50abe002d2d607def6d8496d616033693
SUPERSEDES: test-hub/findings/20261005-1815-tiktok-central-session-restore.md

## Objetivo
Verificar por que a correção de restore central não alterou os testes seguintes.

## Resultado
A listagem real de deploys mostrou que o serviço ainda estava live em ab3565d8. O commit cdd656b5 nunca tinha sido implantado; portanto nenhum teste posterior poderia validar seu restore. O deploy correto foi agora disparado via API.

## Evidência decisiva
Render list_deploys: último live dep-db21rd2jnfac73ejbf6g commit ab3565d8. Novo deploy dep-db224ee7bikc73c5npe0 criado para cdd656b5, estado inicial build_in_progress.

## Consequência
Não atribuir a cdd656b5 falhas observadas antes de dep-db224ee7bikc73c5npe0 ficar live. Após live, testar em paralelo somente leitura: revisão/health, OIDC, central session availability, restore, local state, identity e readiness. Não publicar.
