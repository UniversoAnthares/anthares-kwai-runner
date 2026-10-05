# Kwai publicador recusa jobs sem intervalo canônico
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: f5b38205db3a764804a561d869cbb3f0ca654dcc
SUPERSEDES: none

## Objetivo
Fechar a possibilidade de a rota central do publicador Kwai contornar a deduplicação temporal.

## Resultado
O workflow kwai-real-publish agora exige source_id, source_start e source_end em todo job obtido da fila central. Também valida end > start. Job legado/sem intervalo é recusado antes de download, login ou publicação.

## Evidência decisiva
Commit f5b38205db3a764804a561d869cbb3f0ca654dcc adiciona fail-closed no ponto de lease da fila: ausência ou intervalo inválido termina a execução antes do publisher.

## Consequência
Nenhuma publicação Kwai vinda da fila central pode avançar sem identidade e intervalo temporal canônicos. Produtores da fila devem fornecer esses campos. A entrada manual workflow_dispatch permanece explicitamente manual e fora da automação de geração.
