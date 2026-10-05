# Declared login activities are internal-only
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388231997
JOB: 112026820151
COMMIT: a0cda10864a4c165d28482989bed90dc3d17d71d
SUPERSEDES: test-hub/findings/20261006-0020-lease-kwai-declared-login-activity-probe.md

BASELINE_PROVEN: test-hub/findings/20261006-0018-kwai-manifest-login-components-proven.md
SUCCESS_SIGNAL: declared login Activity starts and exposes auth UI.
FAILURE_SIGNAL: every selected declared Activity rejected or starts without auth UI.
TEST_VALIDITY: Kwai installed, adb package check passed, am start results logged for all targets.

## Objetivo
Testar diretamente as Activities reais de login declaradas no Manifest.

## Resultado
FAILURE_SIGNAL=ALL_DECLARED_ACTIVITIES_REJECTED. EmailLoginActivity, LoginActivity, CommonLoginActivity, PhoneAccountActivityV2 e SplashLoginActivity retornaram SecurityException: Permission Denial ... not exported from uid 10209.

## Evidência decisiva
Todos os cinco alvos retornaram AM_RC=255 e START_ALLOWED=False por not exported. O probe completou sua lógica e saiu 20.

## Consequência
Direct am start via shell está encerrado para estas Activities. O próximo caminho deve entrar pelo fluxo interno do próprio app: identificar componentes exportados/deep links/aliases que encaminhem para login, ou reproduzir o evento interno a partir de MAIN. Não repetir direct-launch destes cinco nomes.
