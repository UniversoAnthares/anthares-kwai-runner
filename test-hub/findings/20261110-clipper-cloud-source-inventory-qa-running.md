# CORTES — inventário de cronologia WordPress/YouTube exclusivamente leitura
STATUS: RUNNING
AREA: cortes-source-inventory
DATE: 2026-11-10
OWNER: chatgpt-clipper-cloud-repair-20261110
SOURCE_RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/42833152004
SUPERSEDES: none

## Observações
- Três runs do cortes-daily em 10/11 falharam ao selecionar fonte com CORTES_SOURCE_INCOMPLETE_ACTIVE_STREAMS_INVENTORY:1.
- Todos os três executaram no DESKTOP-FTDK0HP, contrariando a meta de produção independente.
- Inventário WordPress da origem permanece protegido; leitura da API com credenciais WP_QA existentes é a única operação autorizada pelo novo workflow.
- A comparação YouTube/WordPress é somente leitura e imprime IDs públicos e estados sanitizados de fontes pendentes.
- Nenhum produtor, cron, fila, token, mídia ou arquivo WordPress será alterado por esta instrumentação.

## Aceite pendente
- Executar job no ubuntu-24.04.
- Identificar a fonte ativa ausente sem suprimir cronologia, alterar estado ou fazer upload.
- Escolher recuperação com origem legítima verificável e preparar execução de geração na nuvem sem trocar escritor ativo.
