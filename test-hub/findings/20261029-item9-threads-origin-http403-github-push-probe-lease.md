# Item 9 — diagnóstico isolado de HTTP 403 na origem GitHub Actions
STATUS: RUNNING
AREA: threads/cloud-media-403
DATE: 2026-10-29 UTC
RUN: none
JOB: none
COMMIT: source main 9e2071ec6a80d573f489a36db7d534aa5011c285
SUPERSEDES: none
LEASE: branch fix/threads-origin-403-push-probe-20261029-9e2071e; only .github/workflows/cortes-threads-cloud-handoff.yml push-only read probe; expires on merge/results.

## Objetivo
Uma única requisição GET Range (1 KiB) do runner GitHub-hosted ao MP4 real short_fOmihuHUT1M_g1_7868_7908.mp4 que recebeu MEDIA_HTTP_403 em 2026-10-28 23:43 UTC; imprimir HTTP status e header x-hcdn-request-id. Origem Hostinger já confirmou arquivo existente; Windows HTTP 200/206. Nenhuma publicação e nenhuma alteração no Neon/CDN/segredos.

## Causalidade
Neon em 2026-10-29 17:31 UTC: 195 confirmed, 99 queued, 98 MEDIA_HTTP_403 isolados e 1 EDITORIAL_MISSING isolado; cloud_primary_enabled=false. Não liberar quarentena sem prova independente e validação editorial/media_sha256. Apenas evento push main executará o probe, cron não o executa.

## Segurança e concorrência
Preservar a exclusão mútua existente, todas as publicações originais, outros trabalhos e marcadores P0; não armar cloud, não publicar, não tocar a quarentena. Resultado HTTP 200/206 em um objeto não autoriza liberar outros 98.
