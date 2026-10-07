# Kwai clear-data — PROVEN session reset; login surface optional on MAIN
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37639930771
JOB: 112855863788
COMMIT: 8b930dced003086acca1051dc50b045f204d7f84
SUPERSEDES: 20261007-kwai-clear-data-partial-interest-stuck.md

## Objetivo
Após sessão cached, forçar superfície de login via pm clear.

## Resultado
FUNCIONOU (PROVEN):
- pm clear Success
- TEST_VALIDITY=OK
- Pós-clear: INTEREST → START → RESOURCE_LOADING → MAIN (kwai_ctx=True)
- Sessão autenticada cached é removida; onboarding fresco executa

NÃO atingido (não é FAILED da hipótese de reset):
- LOGIN_SURFACE_FORCED=0 — o Kwai permite MAIN anônimo; login não é obrigatório após clear
- Exit 21 = ausência de UI de login no caminho pós-clear, não falha de harness

## Evidência decisiva
post-clear-13 state=START → post-clear-14/15 RESOURCE_LOADING → post-clear-16 MAIN
`[CLEAR] reached MAIN after clear without login surface`

## Consequência
- Tratar `pm clear` como ferramenta PROVEN de reset de sessão (usar antes de autologin quando houver cached account).
- NÃO repetir clear-data esperando LOGIN_SURFACE automático.
- Próximo caminho causal para READY: a partir de MAIN anônimo, usar o controle semântico de login já PROVEN em run 37417286394 (LOGIN_CONTROL_VISIBLE / Welcome to Kwai / phone / Google / Facebook), tipicamente via Profile ou botão Log in no MAIN.
- Autologin credentialed só depois de reexpor esse controle.
