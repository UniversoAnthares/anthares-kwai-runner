# State Driver normaliza onboarding em 8 de 10 réplicas; launcher fica sem recovery
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384859435
JOB: 10 state-driven replicas
COMMIT: edfe07291132b4daec51018a7b9fd07ddce93977
SUPERSEDES: test-hub/findings/20261005-2358-state-driver-replicas-running.md

## Objetivo
Normalizar estados variáveis do onboarding antes de testar Profile, usando FSM PERMISSION/INTEREST/START/MAIN/OTHER.

## Resultado
O run agregado terminou failure, mas 8 jobs concluíram success e chegaram a FSM_MAIN_REACHED. Uma réplica foi cancelada. A réplica 8 falhou porque o diálogo Android "Pixel Launcher isn't responding" foi classificado repetidamente como OTHER até FSM_TIMEOUT. Nas réplicas válidas, o FSM atravessou INTEREST (quantidades variáveis 6/9/12), START e MAIN, encontrou PROFILE_PARENT=True e, após Profile, reproduziu o DFM "resource downloading".

## Evidência decisiva
Jobs 1,2,3,4,5,7,9,10: FSM_MAIN_REACHED e PROFILE_PARENT=True. Job 8: FSM 0..44 STATE=OTHER UI="pixel launcher isn't responding" -> FSM_TIMEOUT. Job 6: cancelled. Réplicas válidas exibem POST_PROFILE_UI com resource downloading.

## Consequência
A FSM state-driven passa a ser baseline PROVEN/PARTIAL para travessia; não voltar a matrizes pré-normalização. Próxima alteração causal é exclusivamente adicionar estado/recovery para diálogo Pixel Launcher e repetir somente validação de robustez necessária. Profile/DFM continua bloqueio posterior conhecido; não abrir nova matriz de login até a travessia estar robusta.

BASELINE_PROVEN: FSM atravessa INTEREST->START->MAIN em 8 réplicas válidas deste run.
FAILED_AVOIDED: matrizes antigas ramificavam antes de normalizar estado; esta FSM decide por estado observado.
SUCCESS_SIGNAL: FSM_MAIN_REACHED após recuperar launcher quando presente.
FAILURE_SIGNAL: launcher persiste após recovery explícito ou FSM_TIMEOUT em estado reconhecido.
TEST_VALIDITY: falha de boot/ADB/cancelamento/harness não conta contra a hipótese.
