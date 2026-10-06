# QA: Android Agent build failures are harness-only; agent code not tested
STATUS: PARTIAL
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396743483 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396753682
JOB: 112054423063 ; 112054452765
COMMIT: 15977698b0c2f864d6671387ea675061d63fed65
SUPERSEDES: none

## Resultado
Os dois builds falharam dentro de android-actions/setup-android antes de Gradle/compilação do Agent. A action executou `sdkmanager tools`, pacote inexistente no SDK atual, e abortou com `Failed to find package 'tools'`.

## Evidência decisiva
Ambos os jobs terminam no mesmo ponto: `/cmdline-tools/16.0/bin/sdkmanager tools` -> Warning: Failed to find package 'tools' -> setup-android exit code 1. Nenhum erro Kotlin/Manifest/Gradle do Agent foi alcançado.

## Consequência
Não classificar Android Agent como falho. Corrigir o workflow/harness removendo a solicitação legada `tools` e usar os cmdline-tools já presentes / pacotes explícitos necessários. Só depois um build pode testar a fundação do Agent.