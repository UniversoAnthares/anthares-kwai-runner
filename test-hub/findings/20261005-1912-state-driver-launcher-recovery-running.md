# Launcher-recovery validation queued on proven state driver
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: state-driven replicas
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1902-kwai-state-driver-8-of-10-proven.md
FAILED_AVOIDED: test-hub/findings/20261005-1908-state-driver-8of10-launcher-gap.md; LAUNCHER_ANR agora é estado explícito, com fechamento/espera do diálogo, force-stop e relaunch do Kwai.
SUCCESS_SIGNAL: FSM_MAIN_REACHED nas réplicas, inclusive após LAUNCHER_ANR quando ele ocorrer.
FAILURE_SIGNAL: FSM_TIMEOUT após recovery explícito de LAUNCHER_ANR.
TEST_VALIDITY: boot/ADB/cancelamento externo não refuta o recovery.

## Objetivo
Validar somente a correção causal do único estado que derrubou a robustez observada da FSM.

## Resultado
Aguardando execução.

## Evidência decisiva
Aguardando.

## Consequência
Não abrir matriz concorrente de onboarding/login enquanto este teste causal estiver RUNNING.
