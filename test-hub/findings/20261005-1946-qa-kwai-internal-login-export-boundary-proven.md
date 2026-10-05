# Direct start of internal Kwai login Activities is blocked by Android export boundary
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388231997
JOB: 112026820151
COMMIT: a0cda10864a4c165d28482989bed90dc3d17d71d
SUPERSEDES: test-hub/findings/20261006-0020-lease-kwai-declared-login-activity-probe.md

BASELINE_PROVEN: test-hub/findings/20261006-0018-kwai-manifest-login-components-proven.md
SUCCESS_SIGNAL: internal login Activity starts and exposes login UI.
FAILURE_SIGNAL: selected Activities rejected by Android or start without login UI.
TEST_VALIDITY: package/install/ADB executed; each am start result was logged.

## Objetivo
Classificar corretamente o direct Activity probe sem confundir export boundary com inexistência de login.

## Resultado
PROVEN apenas para a fronteira Android: adb shell não pode iniciar diretamente as cinco Activities selecionadas. Todas foram rejeitadas com SecurityException Permission Denial / not exported. Nenhuma UI de login foi executada, portanto a hipótese de existência/funcionamento da UI interna continua não testada.

## Evidência decisiva
Job 112026820151: EmailLoginActivity, LoginActivity, CommonLoginActivity, PhoneAccountActivityV2 e SplashLoginActivity retornaram AM_RC=255 e `not exported from uid 10209`; o harness terminou `FAILURE_SIGNAL=ALL_DECLARED_ACTIVITIES_REJECTED`.

## Consequência
Não repetir `adb shell am start -n` contra essas Activities. O próximo teste kwai-login deve mudar causalmente para um gateway exported/deeplink que leve internamente ao login, navegação normal instrumentada, ou Anthares Agent/Accessibility dentro do fluxo oficial. O resultado NÃO autoriza declarar login impossível nem descartar as Activities internas.