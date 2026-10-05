# TikTok diagnostic cadence is functionally aligned with hub
STATUS: PROVEN
AREA: tiktok-publish
DATE: 2026-10-05
RUN: static
JOB: none
COMMIT: 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79
SUPERSEDES: test-hub/findings/20261005-1958-chat3-tiktok-diagnostic-cadence-cleanup-lease.md

BASELINE_PROVEN: hub vigente mantém diagnóstico TikTok em 3 posts/dia com espaçamento de 3–6 horas; canário permanece bloqueado por sessão.
FAILED_AVOIDED: comportamento executável não foi alterado; 61–300 s não foi restaurado durante diagnóstico; nenhuma publicação foi disparada.
SUCCESS_SIGNAL: planner executável usa MIN_SCHEDULE_GAP_SECONDS=10800 e MAX_SCHEDULE_GAP_SECONDS=21600 com timezone America/Campo_Grande; workflow usa TIKTOK_DAILY_TARGET=3; valores antigos TIKTOK_NEXT_MIN_SECONDS/TIKTOK_NEXT_MAX_SECONDS não possuem consumidores encontrados no repositório e não comandam o planner.
FAILURE_SIGNAL: qualquer caminho executável usar 61–300 s, 60–90 s ou target 100 durante o diagnóstico vigente.
TEST_VALIDITY: leitura direta do youtube_tiktok_pipeline.py em main e busca de consumidores das variáveis antigas. Esta prova cobre lógica/configuração estática; throughput real depende de produção confirmada.

## Objetivo
Verificar se sinais textuais antigos poderiam alterar a cadência diagnóstica atual.

## Resultado
PROVEN funcionalmente. youtube_tiktok_pipeline.py define 10800–21600 segundos e calcula next_publish_at a partir desse intervalo. O workflow fixa TIKTOK_DAILY_TARGET=3. Duas variáveis antigas 60/90 e comentários históricos sobre 61–300 permanecem como texto/configuração inerte; a busca não encontrou consumidor dessas variáveis. Não foi feita mutação cosmética para evitar novo churn sem efeito operacional.

## Consequência
LEASE tiktok-publish encerrado. Política operacional atual continua 3 posts/dia, 3–6 horas, até finding posterior encerrar o diagnóstico de distribuição. Quando isso ocorrer, a restauração de 100/dia e 61–300 s deverá ser feita como experimento causal próprio, com lease novo e validação de produção.
