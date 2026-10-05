# First ten-way onboarding matrix was invalid
STATUS: FAILED
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37372686273
JOB: multiple
COMMIT: none
SUPERSEDES: none

## Objetivo
Comparar dez estratégias de travessia do onboarding em paralelo.

## Resultado
O teste não mediu as estratégias. O android-emulator-runner separou o heredoc Python; linhas como import foram executadas pelo shell e falharam com exit 127. Outros jobs foram cancelados.

## Evidência decisiva
Log: /usr/bin/sh: 1: import: not found.

## Consequência
Nunca interpretar esse run como baseline/permission/activity etc. falhando. Scripts Python complexos devem existir como arquivos executáveis, não heredoc dentro de script do android-emulator-runner.
