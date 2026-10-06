# Lease: control renew heartbeat contract
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Objetivo
Provar que o renew v14 suporta heartbeat periódico repetido sem permitir ressurreição de lease expirado, troca de owner ou renovação fora de leased. Camada independente dos publishers Kwai/TikTok.

## BASELINE_PROVEN
Worker v14 PROVEN EM PRODUÇÃO; run 37394732038 prova owner-only renew, extensão simples, rejeição de estado inválido e expirado, além de single-job double-claim.

## FAILED_AVOIDED
Não editar publicadores Kwai/TikTok enquanto seus leases estiverem ativos. Não usar PC como runtime. Não reabrir deploy público sem CLOUDFLARE_API_TOKEN.

## SUCCESS_SIGNAL
Self-test autenticado prova duas renovações sucessivas com lease_until estritamente crescente; owner incorreto continua rejeitado; job fora de leased e expirado continuam rejeitados; self-test integral HTTP 200.

## FAILURE_SIGNAL
Renew repetido não aumenta lease_until, owner incorreto consegue renovar, lease expirado revive, ou regressão em qualquer invariante já PROVEN.

## TEST_VALIDITY
Usar apenas jobs __selftest_* isolados e cleanup final. Falha de OIDC/deploy/harness é INVALID/NOT_TESTED.

## Lease
MUTATION_AREAS: cloudflare-control
EXPIRES: 2026-10-05T21:10:00-04:00
