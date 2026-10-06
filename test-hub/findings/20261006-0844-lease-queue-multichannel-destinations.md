# Lease — multichannel destination model for Distribuidor Anthares
STATUS: RUNNING
AREA: queue
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Generalizar o Distribuidor WordPress de provider único para destination_key = platform:account_id, preservando fila, fencing, heartbeat, dedupe, UNCERTAIN, reconcile e confirmation_evidence; preparar adaptadores kwai:secondary, instagram:primary, threads:primary e x:primary sem publicar canários antes de autenticação/identidade confirmadas.

## Lease
OWNER: chatgpt-social-destinations
EXPIRES: 2026-10-06T13:14:00Z
SCOPE: anthares-tiktok-distributor e contratos de destino; nenhuma mutação de sessão Kwai principal/TikTok existente.

## BASELINE_PROVEN
Cloudflare control plane v16: lease_generation, renew/heartbeat, fail-closed complete/reconcile, UNCERTAIN e circuit breaker PROVEN. WordPress atual possui fila comum e delivery por provider, porém provider não inclui account_id.

## FAILED_AVOIDED
Não repetir rotas Kwai authorization/login já FAILED; não tocar kwai:primary durante teste secundário; não considerar HTTP isolado confirmação; não criar filas independentes por rede.

## SUCCESS_SIGNAL
Schema e API aceitam platform+account_id, dedupe por mídia+destino, estados individuais e confirmation_evidence, com compatibilidade migratória para tiktok:primary/kwai:primary e testes estáticos/locais passando.

## FAILURE_SIGNAL
Migração perde entregas existentes, permite colisão entre contas, ou qualquer complete ocorre sem prova independente exigida.

## TEST_VALIDITY
HEAD relido após criação do lease; qualquer lease queue ativo anterior e não expirado invalida mutações. Testes reais ficam bloqueados até identidade READY por destino.
