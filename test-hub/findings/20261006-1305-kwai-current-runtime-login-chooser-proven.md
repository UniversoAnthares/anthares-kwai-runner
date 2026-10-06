# Kwai current runtime — MAIN and app-native login chooser proven
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37464807237
JOB: 112273064941
COMMIT: dc83ad0930321d0703c49609658d5691bb47a6e4
SUPERSEDES: test-hub/findings/20261006-kwai-install-proven-accessibility-current-blocker.md

## Objetivo
Validar o executor Android atual depois do blocker de AccessibilityService e alcançar semanticamente a superfície real de login do aplicativo.

## Baseline
Instalação Kwai+Agent e KVM já PROVEN. Rotas Activity/URI diretas permanecem descartadas.

## Resultado
O serviço de Accessibility continuou sem bind, porém o fallback UIAutomator tornou esse blocker irrelevante para a cadeia atual. O runtime alcançou FSM_MAIN_REACHED, encontrou exatamente um controle Login, acionou-o semanticamente e observou a tela app-native: "Welcome to Kwai", "Continue with Google", "use Facebook", "Phone".

## Evidência decisiva
TEST_VALIDITY=EMULATOR_BOOTED
TEST_VALIDITY=APPS_INSTALLED
AGENT_SERVICE_UNAVAILABLE_UIAUTOMATOR_FALLBACK
FSM_MAIN_REACHED
LOGIN_CONTROL_COUNT=1
LOGIN_CONTROL_VISIBLE=1
AUTH_EXPLICIT_CONTROLS=1
SUCCESS_SIGNAL=LOGIN_SURFACE_REACHED

A etapa opcional Studio/Chrome ficou presa no Chrome FRE e não altera a prova app-native.

## Consequência
Preservar UIAutomator como fallback canônico. O próximo passo causal é acionar semanticamente Phone dentro do app e parar em Phone/OTP/challenge; não repetir rotas diretas nem tratar Accessibility binding como blocker. KWAI_LOGIN_READY ainda exige autenticação e identidade independente da conta.
