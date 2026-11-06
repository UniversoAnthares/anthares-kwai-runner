# AOI item #14 — publicação real TikTok histórica comprovada
STATUS: PROVEN
TERMINAL_STATE: DONE
ITEMS: [14]
AREA: tiktok-historical-real-post-acceptance
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T18:41:55.172Z
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40415232407
JOB: 121895778546
SOURCE_COMMIT: 513c8f4015a1c40c7a070f1648b1bb136e163e58
SOURCE_BLOB: c62544773c982a60b2b470f068a4c9dcb437ad8d
SUPERSEDES: 20261104-aoi14-tiktok-historical-real-post-running-lease.md
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_AREA: tiktok-historical-real-post-acceptance
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90
PRODUCTION_CHANGE: NONE
COST_ADDED: 0

## Critério original
Item fixo #14: “Publicação real TikTok homologada — Prova histórica de publicação real com identidade correta; não inferir migração Forgejo”. Resultado terminal observado para a conta @lucasrosalem4, em executor GitHub hospedado. Item #15, que exige AMBOS os publicadores pelo novo executor, permanece PARTIAL. Não reivindicar migração para Forgejo nem funcionamento atual.

## Prova direta, três sinais concordantes
1. GitHub Actions (run 40415232407, job 121895778546), 2026-10-26T22:48:44–22:49:09Z, conclusão SUCCESS: na etapa de execução real `python3 -u tools/cortes_tiktok_lucasrosalem4_cloud_publish.py`, o log contém, em ordem, `SECONDARY_CLOUD_QUEUE_BACKEND=neon`, `SECONDARY_CLOUD_QUEUE_READY=1`, `SECONDARY_CLOUD_IDENTITY_VERIFIED account=lucasrosalem4 existing=5`, `SECONDARY_CLOUD_PRESTART_STAGE=verified`, `SECONDARY_CLOUD_IRREVERSIBLE_FENCE=1`, `SECONDARY_CLOUD_CONFIRMED=https://www.tiktok.com/@lucasrosalem4/video/7701112271417724212`. É etapa produtiva separada das simulações anteriores do unittest. Link: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40415232407/job/121895778546.
2. Neon read-only em 2026-11-04, tabela `public.cortes_tiktok_lucasrosalem4_publications`, lookup exato do remote_id `7701112271417724212`: `status=confirmed`, `confirmed_at=2026-10-26T22:49:09.491Z`, `publication_started_at=2026-10-26T22:49:02.942Z`, `lease_generation=2`. O timestamp de confirmação e ID coincidem com o job produtivo GitHub Actions.
3. Fonte do executor na revisão exata do run, arquivo `tools/cortes_tiktok_lucasrosalem4_cloud_publish.py` com blob `c62544773c982a60b2b470f068a4c9dcb437ad8d`, igual ao main GitHub atual e peer GitLab. O código exige verificação de identidade no TikTok Studio da conta, fence irreversível confirmado pelo Neon ANTES do botão de publicação, confirmação UI, inventário Studio ANTES/DEPOIS com exatamente um novo vídeo cujo título contém o marcador esperado e está ausente do inventário anterior, então confirmação de id pelo servidor Neon com `lease_generation` idêntico. Qualquer ausência/múltiplos IDs falha fechado.

## Escopo e limitações
- Essa é prova histórica suficiente do item #14. URL pública TikTok não foi acessível anonimamente pelo pesquisador em 2026-11-04 (responde “Site Maintenance”), portanto não declarar visibilidade pública presente nem verificação pública atual. A verificação remota independente ocorreu no próprio TikTok Studio autenticado na execução produtiva, vinculada ao ID na fila Neon.
- Neon também registra 414 `confirmed` para @universo.anthares e 115 para @lucasrosalem4, todos com remote_id e confirmed_at, além de 10 uncertain em @universo.anthares e 2 closed_unverified de @lucasrosalem4. Essas contagens corroboram histórico mas não suprem aceitação do #15 nem autorizam reenvio.
- Nenhum envio, teste de mídia, credencial, scheduler, runner, espelho, segredo, gasto ou fila foi alterado neste encerramento documental. A listagem original de 21 itens permanece fixa; #15 não é promovido.
- Rollback: reabrir estado #14 para PARTIAL somente se surgir evidência contraditória sobre a publicação registrada, com finding e SHA. Não apagar o recibo histórico.

VERDICT: item14 DONE, independent of item15 and Forgejo.
