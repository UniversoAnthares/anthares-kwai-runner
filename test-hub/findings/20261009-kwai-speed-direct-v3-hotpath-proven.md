# Kwai speed direct AVD v3 hot path proven
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37930954196
JOB: attempt1 113821246079; attempt2 113822098028
COMMIT: 1ca64d7cc75dad3d7ed38c9c168a434d4b0004e3
SUPERSEDES: none

## Resultado
O cache direto `kwai-speed-avd-direct-android35-v3` foi construído a partir do full-state v2 e validado em um segundo GitHub-hosted runner independente. A tentativa 2 teve cache hit direto, pulou o archive v2 e a extração interna, carregou realmente `kwai-ready`, chegou a boot_completed em 5 segundos e completou o fast path em 42 segundos.

## Evidência decisiva
- Runner independente attempt 2: eastus, Worker ID distinto.
- `Cache hit for: kwai-speed-avd-direct-android35-v3`
- `DIRECT_AVD_CACHE_HIT=true`
- `AVD_READY_BEFORE_SDK_SECONDS=18`
- `CROSS_RUN_SNAPSHOT_BOOT_SECONDS=5`
- `CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true`
- `Successfully loaded snapshot 'kwai-ready' using 2370 ms`
- `FASTPATH_TOTAL_SECONDS=42`
- `FASTPATH_RESULT=PROVEN_SUB10`
- Hosted runner base: `RUNNER_BASE_EMULATOR_PRESENT=0`, `RUNNER_BASE_SYSTEM_IMAGE_PRESENT=0`; portanto os caches de system image e emulator continuam necessários.

## Comparação
Baseline anterior do workflow de benchmark: TOTAL_SECONDS=88 com cold boot deliberado. O novo caminho quente remove cold boot/regeneração e reduz o total para 42 s, preservando prova de snapshot real entre runners.

## Consequência
Preservar v3 como baseline PROVEN. Próxima otimização deve reduzir bytes restaurados. Inventário run 37931381381 mostrou dois snapshots RAM duplicando ~1,319 GB cada; `default_boot` pode ser removido em experimento causal, mantendo `kwai-ready` + estado de disco completo. Não regressar ao snapshot-only de 947 MB, que já falhou por ausência do estado de device/cache.

## Coordenação
Somente kwai-speed. Nenhum arquivo do agente de login alterado. Nenhum PC local usado.
