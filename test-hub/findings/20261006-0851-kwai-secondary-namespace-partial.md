# Kwai secondary namespace ready; authentication blocked on secondary credentials
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: none
JOB: qa-secondary-shell-host
COMMIT: 26d83296ccb37c95463cfdf2e3a771cf6e11e686
SUPERSEDES: test-hub/findings/20261006-0848-lease-kwai-login-secondary-account.md

## Resultado
O mesmo workflow de autologin agora recebe account_id primary|secondary. Seleção de secrets é fail-closed e não possui fallback entre contas. kwai_session_state.sh usa arquivo criptografado separado por account_id. YAML parse passou; bash -n e py_compile passaram em clone fresco Linux.

## Bloqueio concreto
GitHub contém KWAI_LOGIN/KWAI_PASSWORD da conta existente e não contém KWAI_SECONDARY_LOGIN/KWAI_SECONDARY_PASSWORD. Sem identidade própria da conta secundária, KWAI_SECONDARY_LOGIN_READY e REAL_POST não podem ser declarados.

## Consequência
Adicionar apenas os dois secrets secundários (ou concluir login interativo secundário em sessão isolada) e executar o workflow com account_id=secondary. Nunca usar primary como fallback.
