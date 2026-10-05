# Corrected login activity metadata probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: static metadata probe
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1858-kwai-login-activities-crossref.md
FAILED_AVOIDED: run 37384917974 was invalid because aapt was absent while the shell used "|| true"; corrected probe resolves aapt from ANDROID_HOME build-tools and fails if unavailable.
SUCCESS_SIGNAL: manifest metadata printed for at least one known login activity, including exported/enabled/intent-filter context.
FAILURE_SIGNAL: known DEX login classes exist but none are declared as manifest activities/components.
TEST_VALIDITY: AAPT_PATH must exist and command must execute successfully; absence or parser failure exits nonzero and is classified as harness failure.

## Objetivo
Determinar com ferramenta válida se as classes de login já encontradas no APK são componentes Android declarados/iniciáveis.

## Resultado
Aguardando execução.

## Evidência decisiva
Aguardando execução.

## Consequência
Não tentar iniciar activity diretamente até este probe determinar a declaração/exportação.
