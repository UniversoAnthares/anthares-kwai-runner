# CORTES — TikTok restabelecido e inventário social autenticado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-21
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39607994806
JOB: 119249115708
COMMIT: aa53842d18026219ca612ff75f1923b586206e86
SUPERSEDES: none

## Objetivo
Resolver falhas no produtor TikTok e verificar habilitações sociais no WordPress autenticado sem publicar testes nem expor segredos.

## Resultado
TikTok contract run 39603574436 falhou por teste obsoleto SOURCE_EXCEEDS_EXPECTED_LIMIT. O produtor real run 39603574718 e novamente 39606999722 falharam com ValueError antes de concluir lote. PRs Clipper #110 e #113 removeram expectativa de teto, adicionaram rotação de lotes, classificação do erro por origem, reparo Unicode no título e quarentena por item. Run 39607994806 SUCCESS: CORTES_TIKTOK_LEDGER_TITLE_QUARANTINED=1, EDITORIAL_TITLES=222, PRODUCER_OK sources=19 eligible=25 examined=25 created=0, network_enabled=1. Testes locais 8/8 e contrato CI 39607994892 SUCCESS. Filas Neon mantidas sem reset.

## Auditoria autenticada de habilitações
Run https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39607593281 SUCCESS, read-only GET WP state / TikTok OIDC queue health. WP network catalog: enabled=true kwai,tiktok,facebook (Facebook account connection ready, types sem short); enabled=false youtube,instagram,threads,x,pinterest,linkedin,bilibili,odysee,rumble,bluesky,reddit. Threads tem publicações observadas pelo proprietário mas catalog enabled=false; investigar divergência com configuração própria WordPress. Auditoria concluiu OIDC/TikTok Neon authenticated health PASS.

Neon read-only: cortes_tiktok_publications confirmed=133 queued=25 no momento da consulta, e cortes_publications kwai:lucasrosalem confirmed=177 queued=1 uncertain=2 (mais QA keys). Pinterest e LinkedIn sem destinos de produção registrados no ledger. Sem deduzir desabilitação física a partir apenas de catálogo ou dados de uma tabela.

## Evidência e limites
TikTok produtor voltou a SUCCESS, mas RUN created=0 porque jobs já estavam enfileirados; não afirmar que houve novos posts nesta execução. O root cause Unicode do ValueError é fortemente sustentado pela quarentena de 1 título e sucesso subsequente. A habilitação YouTube em catalog false não demonstra suspensão do publicador longo independente. Instagram/Threads têm caminhos autônomos no WordPress; status do catálogo não comprova o token/config interna. Facebook Reels pode estar ativo via módulo separado apesar de catálogo types sem short.

## Consequência
Preservar isolamento de títulos malformados por item, impedir texto corrompido na rede, manter contagem ilimitada da fonte com lotes seguros; auditar reconciliacão Threads e Facebook antes de considerar todos os destinos regulares. Não repetir casos antigos como restrição de 200 clipes.
