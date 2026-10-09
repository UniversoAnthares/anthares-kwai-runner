# Lease — Kwai speed direct-cache fast path v3
STATUS: RUNNING
AREA: kwai-speed
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: baseline 81b82a60da43f99c496599aee3ee158b8af4963f
SUPERSEDES: none
LEASE_EXPIRES: 2026-10-09T09:02:00-04:00

## Objetivo
Reduzir o tempo total do Android snapshot fast path após a prova de carregamento cross-run em 4 segundos, sem tocar em kwai-login, sessão, publicação ou PC local.

## BASELINE_PROVEN
20261008-kwai-speed-cross-run-snapshot-proven.md: cache full AVD v2 restaurado em runner independente; snapshot kwai-ready realmente carregado; boot_completed em 4 segundos.

## FAILED_AVOIDED
Não repetir snapshot-only archive que falhou por faltar estado completo do AVD. Não repetir tar do AVD com emulador ativo. Não alterar agente de login. A mudança causal desta rodada é eliminar cold boot/regeneração quando já existe cache válido e testar cache direto de ~/.android/avd para remover a segunda extração do tar interno.

## SUCCESS_SIGNAL
Runner independente restaura cache direto do AVD, loga Successfully loaded snapshot 'kwai-ready', CROSS_RUN_SNAPSHOT_BOOT_SECONDS < 10 e FASTPATH_TOTAL_SECONDS mensurável. Segunda meta: identificar se emulator/system image já existem no runner antes dos caches.

## FAILURE_SIGNAL
Cache direto ausente/corrompido; snapshot não carrega; fallback cold boot; boot >=10 s; ou estado-base do runner insuficiente sem os caches SDK.

## TEST_VALIDITY
O teste é válido somente se usar GitHub-hosted runner, /dev/kvm disponível, cache v2 proven como fallback e log explícito de snapshot load. Falha de cache/harness não conta como falha do snapshot.

## Coordenação
Escopo exclusivo: novo workflow de benchmark kwai-speed e findings kwai-speed append-only. Nenhum arquivo do agente kwai-login será alterado. Nenhum PC local será usado.
