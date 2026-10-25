# CF-02 R07.6 item 19 — Worker staging real, falha HTTP e rollback Cloudflare
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-25
RUN: ARA staging de Anthares Remote / Wrangler 4.149.0 / Cloudflare real
JOB: R07-CF02-STAGING-20261025
COMMIT: 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: test-hub/findings/20261025-cf02-stage-running.md
LEASE_AREA: cf02-anthares-control-isolated-stage
LEASE_OWNER: ChatGPT-CF02
LEASE_STATUS: CLOSED

## Aceite e escopo
Checklist R07.6 posicao 19 CF-02: homologar UM Worker em staging; health real, falha controlada, isolamento e rollback. CONCLUIDO neste pacote autonomo do Worker anthares-control espelhado no nome exclusivo anthares-cf02-stage-r0725. Trabalhadores ARA/TikTok/outros Workers, memoria DO/KV, cron, filas reais e producao de publicacoes NAO foram testados neste pacote.

## Preparacao com controles
Cloudflare account do Anthares: 5c24be052e5144391f73a8e03491e88e, endpoint exclusivo https://anthares-cf02-stage-r0725.anthares1.workers.dev/health .
Preflight Windows policy.py PASS job CF02-STAGING-20261025 (governanca local f6fc9ca59a96e451). Fonte Github anthares-kwai-runner main 183f6a8eda4d2585f6cdd73982984a66df541802; blob index.js 74eb9a1c832bdd751c42abc2633bb99305159eaf. Aplicados somente em sandbox os cinco patches canonicos v17/v18/lease/cleanup/storage e allowlist OIDC do deploy oficial. SHA256 index.js efetivo 74962BAD7893DFECF03ED73BA9C9F0B03C66061F3C90DEF52DBCC54F4BE85E82. Wrangler --dry-run exit 0, "No bindings found.", syntax Node 24 check 0/0. Worker staging sem KV, DO, triggers cron, rotas personalizadas ou secrets, bloqueando endpoints nao read-only.

## Evidencia decisiva
1. Prova de ausencia inicial: wrangler deployments list retorna account 10007 "This Worker does not exist"; logo script novo e nao sobrescrito.
2. Deploy saudavel: "Deployed anthares-cf02-stage-r0725", versao Cloudflare d7d3d49e-1320-4af3-b7cb-27ae3a5844a5. HTTPS staging: GET /health 200, version=2026-10-17-physical-android-v18, persistent_state=false, queue_bound=false; GET /strategy 200; GET /failover-self-test 200; GET /__cf02/probe 200. GET /tiktok/session-state = 401, GET /job/enqueue =403, POST /job/enqueue =405. Zero publicacao.
3. Teste de falha: versao exclusiva e2d3b7ce-10b8-4e56-b424-8d0905482439 implantada apos --dry-run PASS. HTTP GET /health 503, GET /__cf02/probe 503, /strategy 200. Mesmo instante, Worker producao /health = 200, version 2026-10-17-physical-android-v18, queue_bound=true.
4. Recuperacao REAL: wrangler rollback d7d3d49e-1320-4af3-b7cb-27ae3a5844a5 --name anthares-cf02-stage-r0725 --message ... exit 0. Log decisivo "SUCCESS Worker Version d7d3d49e-1320-4af3-b7cb-27ae3a5844a5 has been deployed to 100% of traffic". API deployments list apos rollback exit 0. Health de staging 200, /__cf02/probe 200 rollback_target=healthy, v18, queue_bound=false, persistent_state=false. Producao 200, v18, queue_bound=true. Wrapper local restaurado e SHA comparado ao backup.
5. Nenhuma alteracao em producao, schemas, filas, segredos, credenciais de publicador, branches main ou PR #1346; referencia CAS #1346 com suite QA anterior aprovada 40157117628 segue independente. Nenhum worker produtivo sofreu rollback ou alteracao.

## Limites e consequencia
Aceite CF-02 **CONCLUIDO NO PACOTE AUTONOMO DE UM WORKER**. Nao certificar o comportamento de recursos efetivos KV/DO de producao nem os outros Workers da conta: precisam de homologacao por servico conforme CF-02 original amplo. A branch PR #1346 CAS ainda deve ser integrada por governanca para corrigir receipt em deploy legitimo, sem acionamento de nova publicacao. Divergencia governanca local f6fc9ca59a96e451 vs GitHub main 2e28d54043d6bad1 no INDICE.md foi preservada sem sobrescrita. Codigo de staging manteve rotas estritamente de observabilidade e bloqueou POST de publicador.
