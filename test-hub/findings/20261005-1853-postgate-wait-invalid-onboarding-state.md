# Post-gate wait probe never reached its target state
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37383465572
JOB: test
COMMIT: 8fe6cdacc09fc3de1c34d87d09e009c67723d161
SUPERSEDES: none

## Objetivo
Partir de um estado pós-gate comum, aguardar estabilização e reinspecionar Profile.

## Resultado
O teste não chegou ao estado pós-gate. Ficou 20 iterações no onboarding "Choose like or dislike... 1/9" e encerrou CLASSIFICATION=UNEXPECTED_UI / REASON=Adaptive traversal did not reach main nav. Portanto o vermelho não testa espera de Profile nem DFM.

## Evidência decisiva
ADAPTIVE_0_UI até ADAPTIVE_19_UI permaneceram em "choose like or dislike to let us know you better. 1/9". Não houve main nav, Profile ou tentativa de login.

## Consequência
Não repetir este harness. A travessia precisa ser state-driven e usar os resource-ids comprovados tiny_discovery_like_button/tiny_discovery_dislike_button, Start now e recuperação de permission/launcher antes de qualquer experimento pós-gate.
