# Lease — Kwai current Android Agent runtime
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none
LEASE_OWNER: chatgpt-current
LEASE_EXPIRES: 2026-10-06T13:30:00Z

## Objetivo
Executar a versão atual do executor Android próprio após a correção causal de ativação do AccessibilityService e observar MAIN -> Profile -> superfície de login sem repetir rotas diretas descartadas.

## BASELINE_PROVEN
Kwai + Agent instalam no emulator/KVM; run 37415036743. O blocker específico do run 37415273062 foi AccessibilityService não habilitado/bound. O workflow atual já adiciona --user 0, abre ACCESSIBILITY_SETTINGS, inicializa o agente e possui fallback UIAutomator.

## FAILED_AVOIDED
Não usar Activities exported=false, bare ikwai://login, authorization routes, coordinate spray ou novas matrizes de hipóteses já refutadas. A mudança causal é o workflow atual pós-blocker, com ativação explícita do serviço e fallback semântico.

## SUCCESS_SIGNAL
TEST_VALIDITY=FSM_MAIN_REACHED seguido por LOGIN_SURFACE_REACHED ou estado Phone/OTP/challenge observável; READY exige identidade independente da conta.

## FAILURE_SIGNAL
Falha concreta posterior a APPS_INSTALLED que identifique a camada exata: accessibility, MAIN, Profile ou login surface.

## TEST_VALIDITY
Emulator bootado + APPS_INSTALLED. Falha anterior a isso é harness inválido e não refuta autenticação Kwai.
