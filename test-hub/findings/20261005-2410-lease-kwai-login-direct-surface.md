# Lease kwai-login direct packaged login surface
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
EXPIRES: 2026-10-05T19:35:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2405-state-driver-partial-proven.md; test-hub/findings/20261005-2250-kwai-apk-login-resources.md
FAILED_AVOIDED: não repetir onboarding/profile matrices; FSM normalizada é preservada. O teste seguinte parte de componentes/IDs empacotados e tenta abrir diretamente a superfície de login após MAIN.
SUCCESS_SIGNAL: activity/surface de login aberta com tiny_login_* / auth_token_login_button ou campo editável observável.
FAILURE_SIGNAL: componentes candidatos rejeitados/inexistentes ou retornam à TinyLaunchActivity sem qualquer recurso de login.
TEST_VALIDITY: aapt/apkanalyzer/adb precisam executar sem command-not-found; instalação e FSM_MAIN_REACHED precisam ser comprovadas. Falha de harness não refuta a hipótese.

## Objetivo
Usar a análise estática comprovada para sair do gargalo Profile/resource downloading e alcançar diretamente a superfície de autenticação.

## Resultado
Lease adquirido antes de qualquer nova mutação/teste.

## Evidência decisiva
FSM já alcança MAIN em 8 réplicas válidas; APK contém TinyLoginActivity/TinyUserInfoActivity e recursos tiny_login_*.

## Consequência
Serializar mutações kwai-login até encerramento deste lease.
