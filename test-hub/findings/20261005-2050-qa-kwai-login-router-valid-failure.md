# QA: Kwai login router is validly failed after MAIN
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37395018657
JOB: 112048807824
COMMIT: 5c8b7b72e7b962d1f8af8ca231a80a8f23be2146
SUPERSEDES: none

## Resultado
Este run é causalmente válido: FSM_MAIN_REACHED ocorreu, Profile parent existia, e só então ikwai://login foi entregue ao UriRouterActivity. O router terminou em TinyLaunchActivity/feed, EDITTEXT_COUNT=0 e AUTH_HITS vazio. FAILURE_SIGNAL=LOGIN_ROUTER_NO_AUTH_SURFACE.

## Evidência decisiva
TEST_VALIDITY=FSM_MAIN_REACHED antes do probe; LOGIN_ROUTER_AM_RC=0; Activity=UriRouterActivity; topResumedActivity=TinyLaunchActivity; EDITTEXT_COUNT=0; AUTH_HITS=; FAILURE_SIGNAL explícito.

## Consequência
Fechar a família bare login-router para autenticação nas condições testadas; não repetir ikwai://login sem mudança causal. Como Profile ainda cai em resource downloading, o próximo caminho deve ser interno/agent/accessibility após disponibilidade do módulo, não outro deep link equivalente.