# Cloudflare deploy endurecido aguardando runner
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: eca48b62c1c151a077d119b38a74b9cbe16aa743
SUPERSEDES: none

## Objetivo
Fechar o item 1: publicar a barreira central de sobreposição temporal já implementada no anthares-control.

## Resultado
O workflow de deploy foi endurecido: ganhou workflow_dispatch, id-token write, validação explícita de CLOUDFLARE_API_TOKEN, set -euo pipefail e versão fixada wrangler 4.43.0. O push foi feito no main. Até a consulta imediatamente posterior o GitHub ainda não havia criado run para o novo SHA.

## Evidência decisiva
Commit eca48b62c1c151a077d119b38a74b9cbe16aa743 no main; consulta de runs por head_sha retornou total_count=0 imediatamente após o push.

## Consequência
Aguardar/disparar o run novo e verificar o log antes de classificar o deploy. Não repetir o workflow antigo sem essas correções. Depois do deploy, testar overlap total, overlap de 1 segundo e intervalo inédito.
