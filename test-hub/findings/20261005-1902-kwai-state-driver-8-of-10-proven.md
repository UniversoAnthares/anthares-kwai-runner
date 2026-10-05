# State-driven onboarding reaches MAIN in 8 of 10 replicas
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384859435
JOB: 10 state-driven replicas
COMMIT: edfe07291132b4daec51018a7b9fd07ddce93977
SUPERSEDES: test-hub/findings/20261005-2358-state-driver-replicas-running.md

BASELINE_PROVEN: test-hub/findings/20261005-2210-stabilization-results-restart-proven.md
FAILED_AVOIDED: test-hub/findings/20261005-2350-start-gate-matrix-invalid-state.md; o driver normaliza PERMISSION/INTEREST/START/MAIN em vez de atribuir sucesso a uma variante iniciada em estado diferente.
SUCCESS_SIGNAL: FSM_MAIN_REACHED e PROFILE_PARENT=True.
FAILURE_SIGNAL: FSM_TIMEOUT sem MAIN.
TEST_VALIDITY: estados e transições são impressos; travamento do Pixel Launcher é classificado como falha ambiental/harness e não como refutação da FSM.

## Objetivo
Medir se um controlador orientado pelo estado real consegue atravessar o onboarding variável até MAIN de forma repetível.

## Resultado
8/10 réplicas registraram FSM_MAIN_REACHED e PROFILE_PARENT=True. Réplicas 6 e 8 não chegaram a MAIN: permaneceram em OTHER com "Pixel Launcher isn't responding" até FSM_TIMEOUT; 8 terminou failure e 6 foi cancelled após timeout. Nas oito válidas, a sequência observada foi INTEREST repetido conforme o número variável de telas, START e então MAIN.

## Evidência decisiva
state-driver 1,2,3,4,5,7,9,10: FSM_MAIN_REACHED + PROFILE_PARENT=True. state-driver 6 e 8: Pixel Launcher isn't responding + FSM_TIMEOUT. Exemplos válidos mostram START imediatamente seguido de MAIN e feed real com Home/Discover/Inbox/Profile.

## Consequência
Promover o FSM state-driven como baseline de onboarding, com robustez observada 8/10. Tratar Pixel Launcher travado como falha ambiental recuperável e reiniciar/repetir somente essa réplica. Não voltar a matrizes pré-normalização. O próximo experimento de login deve partir apenas após SUCCESS_SIGNAL FSM_MAIN_REACHED e então usar a evidência estática PROVEN das activities de login.
