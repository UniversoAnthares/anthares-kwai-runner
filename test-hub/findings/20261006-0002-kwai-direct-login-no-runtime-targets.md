# Direct login probe found no runtime component targets
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37386423827
JOB: 112020701870
COMMIT: 1aee051ee9639edc30330d2152fdb49e0edaa690
SUPERSEDES: test-hub/findings/20261005-2410-lease-kwai-login-direct-surface.md

BASELINE_PROVEN: test-hub/findings/20261005-2405-state-driver-partial-proven.md; test-hub/findings/20261005-2250-kwai-apk-login-resources.md
SUCCESS_SIGNAL: login surface with tiny_login/auth_token/EditText.
FAILURE_SIGNAL: candidate components rejected/inexistent or no login surface.
TEST_VALIDITY: Android/install/ADB executed; probe itself ran.

## Objetivo
Abrir diretamente componentes de login empacotados.

## Resultado
O probe terminou exit 30. No código, exit 30 ocorre somente quando TARGET_COUNT=0 após dumpsys package; portanto nenhum dos nomes TinyLoginActivity, TinyUserInfoActivity, TinyGoogleSSOActivity ou AutoLoginActivity foi encontrado como alvo runtime pelo método usado. Nenhum am start foi tentado.

## Evidência decisiva
kwai_direct_login_probe.py: if not targets: raise SystemExit(30). O run terminou nesse código.

## Consequência
Não repetir direct-launch por nomes de classes. Primeiro validar o Manifest com aapt funcional e obter nomes/componentes declarados reais.
