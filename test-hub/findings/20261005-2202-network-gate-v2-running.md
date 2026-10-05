# Focused Android/Kwai network gate probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378882974
JOB: single probe
COMMIT: f9636b8c8e4f3ae180c7613bf02a6cf1666d5a1b
SUPERSEDES: none

## Objetivo
Complementar a matriz de estabilização já em andamento com um probe único e curto que mede DNS/rota no Android e observa o progresso de Resource downloading após a travessia adaptive.

## Resultado
Workflow criado e execução 37378882974 entrou na fila.

## Evidência decisiva
O probe registra DNS/route, resolução de hosts Kwai e cinco checkpoints de UI/progresso, com timeout total de 5 minutos.

## Consequência
Não repetir a matriz profile/login. Comparar este resultado com o run 37378856592 e usar somente a alteração causal que remover o gate de rede/recursos.
