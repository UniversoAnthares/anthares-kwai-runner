# Validated Kwai vault and split set
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37370378251
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Instalar e abrir o APK oficial validado do Kwai no Android remoto.

## Resultado
API35: DEVICE_ABI=x86_64,arm64-v8a; NATIVE_BRIDGE=libndk_translation.so. O conjunto comprovado é com.kwai.video.apk + dfm_ug.apk + config.arm64_v8a.apk + config.xxhdpi.apk. O app chega a KWAI_LAUNCHED.

## Evidência decisiva
Logs reais registraram SELECTED_ABI=arm64_v8a, os quatro splits e KWAI_LAUNCHED.

## Consequência
Não voltar a instalar todos os splits indiscriminadamente nem trocar o conjunto comprovado sem evidência.
