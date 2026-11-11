# CORTES — reparo do produtor em nuvem: validações reais e bloqueios de produção
STATUS: PARTIAL
AREA: cortes-cloud-producer
DATE: 2026-11-11
OWNER: chatgpt-clipper-real-hosted-20261111
SUPERSEDES: test-hub/findings/lease-cortes-hosted-producer-20261111-0300.md
LEASE_STATE: CLOSED
LEASE_SCOPE: fonte ativa, cookies, execução de mídia hospedada e inspeção do ledger
BASELINE_PROVEN: Clipper daily run 42884980144 selecionou cOhqEaY3-08 via Ubuntu; long/batch skipped; fonte antiga A7BsgCe3-oo encerrada, 230 MP4 WordPress preservados.

## Mudanças implementadas
- Clipper PR #265 merged (6ddfc51f956408c50ac3cc2b49bf052ca828c1c0): parser de cookies Netscape preserva entradas #HttpOnly_. CI Ubuntu runs 42949826701 e 42949821688, SUCCESS.
- Clipper PR #267 merged (bb4e4cde689847e17b554360a41ef7997836561c): canário da fonte corrente sob lock WordPress, arquivo efêmero de 12s, proteção contra mídia antiga e sem mutações.
- Clipper PR #268 merged (cbd56a39a64b3eb7b3ccc066827a981372826a7b): importar via módulo Python; corrigiu ModuleNotFoundError na execução 42950541874.
- Clipper PR #269 merged (c151b55f2c8eeca23b8feaf42dd124b99e84bb12): expor apenas códigos de erro de cookie allowlisted, sem segredos.
- Clipper PR #270 merged (b04dfc2ff8fc0e899c06b3ba46b275e63b292fd0): canário reutiliza extrator de mídia delimitada do Clipper (arquivo WP HTTP 206, depois HLS tv_embedded), sem escrever no ledger. CI 42951371335 SUCCESS.
- Workflow manual cortes-cloud-cookie-canary.yml restaurado a disabled_manually depois dos testes; cron diário e publicadores existentes preservados.

## Testes reais e causa comprovada
- Run 42951016929: CORTES_RENDER_YOUTUBE_COOKIE_DOMAIN_MISSING. O segredo YOUTUBE_COOKIES existente não contém linha Netscape válida para youtube.com/.google.com.
- Run 42951439647: o extrator nativo tentou o trecho exato da fonte cOhqEaY3-08; não encontrou arquivo WordPress utilizável como ranged archive; o cliente tv_embedded_hls recebeu youtube_bot_challenge. Parada fail-closed CORTES_BOUNDED_COOLDOWN_REQUIRED=1. ZERO MP4 criado e persistido, ZERO publicação.
- Quatro Google Drives conectados: busca pelo ID exato vazia; pastas preexistentes de backup/arquivo CORTES e output foram inspecionadas em leitura, sem mídia identificada com esse ID. A consulta não é inventário global de todos os destinos existentes.
- Neon projeto purple-flower-35918989, main: zero linhas public.cortes_publications para source_id=cOhqEaY3-08. Snapshot mais recente do ledger revision=15399, capturado 2026-10-31. Tabela cortes_cloud.cortes_short_ledger_head ausente na produção.
- Neon QA br-silent-mud-b8fzvqta possui protótipo CAS PR Clipper #229, role estritamente NOLOGIN. PR #229 draft QA, sem writer LOGIN dedicado, sem segredo isolado no executor, sem handoff nem armazenamento de master homologado.

## Aceite bloqueado
1. Mídia autêntica da fonte atual deve ficar disponível via arquivo externo verificável, ou credencial de leitura YouTube legítima e válida, mantendo cooldown de bot challenge.
2. Autenticar um writer exclusivamente CORTES no Neon com privilégios mínimos e segredo isolado no executor externo, reconciliar head e SHA, provar CAS/fencing sem second writer e sem inventar estado novo.
3. Integrar o renderer real com checkpoint remoto e armazenamento recuperável de master; demonstrar MP4 final válido (30-90s, 720×1280, áudio e editorial), registro no WordPress/Neon e ciclo diário sem PC. Nunca iniciar jobs Windows ou reprocessar a origem encerrada.

## Resultado
PARTIAL: código de parser e canário hospedado implantados, testes sintéticos PASS; os testes de origem real encerraram com falhas externas classificadas. O item de geração diária de novos masters fora do PC permanece OPEN. Nenhuma fila/publicação, mídia original, regra de retenção ou controle de writer produtivo alterado.
