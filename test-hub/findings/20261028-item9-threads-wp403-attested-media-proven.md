# Item 9 — Threads: leitura exata de mídia atestada após HTTP 403
STATUS: PROVEN
AREA: threads/cloud-media-exact-lookup
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40771473806
JOB: 123109868457
COMMIT: 478aa248cccbd141d11fbc6213fe25e67a6ca2f7
SUPERSEDES: test-hub/findings/20261028-item9-threads-wp403-attested-media-lease.md

## Correção causal
O publicador Threads autorizado falhava antes do envio: WORDPRESS_HTTP_403 na consulta exata REST de mídia WordPress, no run #40749020705. A PR #1812 alterou somente o fallback de busca para a mídia pública exata cuja identidade, duração, origem, attachment_id e SHA256 já estejam atestados em config/threads-verified-transcripts.json. O download/sha256 do MP4 e o validador editorial permanecem obrigatórios antes de qualquer claim ou publicação; HTTP 401 e identidade sem evidência continuam bloqueados. Nenhuma autorização WordPress, token, segredo ou produtor alternativo foi alterado.

## Prova executada
- GitHub Actions #40771473806, job #123109868457: SUCCESS, 22 testes, sem upload.
- THREADS_ALLOW_PUBLISH=0 durante prova automatizada em push.
- Saída real de dry-run: ok=true; mode=dry_run; account=universoanthares; clip=threads:fOmihuHUT1M|g1:fOmihuHUT1M:4762:4803; bytes=4805336; media_verified=true; queue_candidates=101; source_day=2026-10-22; published=false.
- A execução de produção preexistente #40771464899 (commit anterior) publicou e registrou no Graph o corte threads:fOmihuHUT1M|g1:fOmihuHUT1M:4722:4762, permalink https://www.threads.com/@universoanthares/post/DfDY5JWjZAr. É prova de operação do publicador principal, não prova de novo post com a correção.
- Gate Neon lido após o merge: confirmed=192, queued=102, failed=1, cloud_inflight=0, cloud_primary_enabled=true, owner=local entre leases, epoch=119, last_success=2026-10-28 21:23:41Z. Conservar a fila e não lançar executor concorrente ou reenvio incerto.

## Limites do resultado
O erro de busca WordPress 403 está corrigido e o vídeo completo com hash foi confirmado na execução real de código em dry-run. O item fixo 9 (publicação de todos os cortes Threads) continua PARTIAL enquanto a fila não for drenada com confirmação individual e respeito ao teto diário vigente. O cron e o fencing Neon permanecem autorizados; não se deve iniciar publicador paralelo. Próxima evidência desejável: run schedule/dispatch após o commit da correção com GRAPH_POSTED e confirmação Neon, nunca só o status success.
