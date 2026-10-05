# CHAT 3 lease — limpeza da cadência diagnóstica TikTok
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-05
RUN: static
JOB: none
COMMIT: 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79
SUPERSEDES: none
LEASE_OWNER: CHAT 3 — TikTok produção/sessão/publicação real/escala
LEASE_START: 2026-10-05T19:58:00-04:00
LEASE_EXPIRES: 2026-10-05T20:13:00-04:00

BASELINE_PROVEN: hub vigente fixa diagnóstico TikTok em 3 posts/dia com espaçamento de 3–6 horas; youtube_tiktok_pipeline.py executa MIN_SCHEDULE_GAP_SECONDS=10800 e MAX_SCHEDULE_GAP_SECONDS=21600; Render está live no publisher 2eb0d9bf e canário segue bloqueado por sessão.
FAILED_AVOIDED: preservar comportamento 3–6h; não restaurar 61–300 s durante diagnóstico; não disparar publish; não tocar em sessão/control plane; não redeployar Render por alteração apenas documental/configuração morta.
SUCCESS_SIGNAL: comentários do planner descrevem 3/dia e 3–6h; workflow deixa de declarar valores antigos 60/90 para variáveis sem uso ou os alinha a 10800/21600; comportamento executável permanece 10800–21600.
FAILURE_SIGNAL: alteração muda constantes executadas, alvo diário diagnóstico, timezone ou lógica de publicação.
TEST_VALIDITY: comparar diff e arquivo final; nenhuma execução real necessária porque a mudança deve ser não funcional ou alinhamento de configuração morta.

## Objetivo
Eliminar sinais antigos de 61–300 s/60–90 s que podem induzir futura regressão durante o diagnóstico atual.
