# Profile-parent rerun blocked by final onboarding gate
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380757409
JOB: login-control-discovery
COMMIT: 1c47615e86fd37648bea780620eabb7d2c119929
SUPERSEDES: none

## Objetivo
Validar clique no pai clicável com.kwai.video:id/ll_profile e descobrir controles de login.

## Resultado
O run falhou antes de chegar ao Profile. A travessia encontrou um gate final de onboarding não tratado: "You’re all set. Hope you enjoy the Kwai!" com botão clicável "Start now" (resource-id com.kwai.video:id/tiny_discovery_left_operation_btn). Como o script só procurava main nav/interesse/swipe, terminou STATE=NO_MAIN_NAV e exit 20.

## Evidência decisiva
NODE=you’re all set. hope you enjoy the kwai! | com.kwai.video:id/tiny_discovery_install_dfm_title
NODE=start now | com.kwai.video:id/tiny_discovery_left_operation_btn | Button | true
STATE=NO_MAIN_NAV; exit code 20.

## Consequência
Não classificar ll_profile como falho. Toda nova rota deve tratar explicitamente Start now/tiny_discovery_left_operation_btn antes de procurar main nav. Ampliar testes paralelos após esse gate, sem repetir a travessia incompleta.
