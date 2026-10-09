# Kwai speed slim AVD v4 proven
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37931602733
JOB: build 113823413308; hot independent 113824074198
COMMIT: 667bbb4cb2f650555c48578e1f956533508cc8b3
SUPERSEDES: none

## Hipótese
O AVD v3 continha dois snapshots RAM de ~1.319 GB cada: `kwai-ready` e `default_boot`. O fast path solicita explicitamente `kwai-ready`; remover somente `default_boot` deve reduzir cache sem repetir a falha antiga de snapshot-only, pois todo o estado de disco/QCOW e config permanece.

## Inventário causal
Run 37931381381 mostrou AVD raw 3,698,916,854 bytes; `kwai-ready` 1,321,606,853 bytes; `default_boot/ram.bin` ~1,318,825,065 bytes; `userdata-qemu.img.qcow2` 814,284,800; `cache.img.qcow2` 142,409,869. O snapshot-only antigo foi rejeitado porque omitia esse estado de disco.

## Build v4
Removido `snapshots/default_boot` = 1,321,607,308 bytes raw. AVD raw caiu para 2,377,309,546 bytes. Cache GitHub v4 salvo com 1,760,052,245 bytes. No mesmo run: `V4_DEFAULT_BOOT_PRESENT=false`, `V4_SNAPSHOT_BOOT_SECONDS=4`, `V4_ACTUAL_LOAD=true`, `Successfully loaded snapshot 'kwai-ready' using 1816 ms`, `V4_RESULT=PROVEN_SUB10`.

## Runner independente quente
Job 113824074198, região westcentralus, Worker ID diferente. Cache hit `kwai-speed-avd-direct-slim-android35-v4`; fallback v3 e save foram pulados. `V4_DEFAULT_BOOT_PRESENT=false`; `V4_SNAPSHOT_BOOT_SECONDS=5`; `V4_ACTUAL_LOAD=true`; `Successfully loaded snapshot 'kwai-ready' using 2809 ms`; `V4_TOTAL_SECONDS=45`; `V4_RESULT=PROVEN_SUB10`.

## Interpretação
v4 reduz o cache AVD em ~953 MB versus v3 e preserva snapshot real entre runners. O total de 45 s nesta amostra não é menor que o melhor v3 (42 s) por variação de throughput; a redução estrutural de bytes é real. Gargalo dominante restante é a imagem Android 35 Google APIs (~1.57 GB no cache), seguida do AVD v4 (~1.68 GiB cache) e emulator (~320 MB).

## Custo/cota
Não criar bundle redundante dos três caches nesta fase: o limite gratuito padrão de Actions Cache é 10 GB/repositório; duplicar ~3.7 GB aumenta risco de eviction/cache-thrashing. Manter componentes separados enquanto se busca uma imagem Android menor.

## Coordenação
Somente kwai-speed; agente de login intacto; nenhum PC local.
