# Launcher recovery hypothesis was not exercised by second matrix
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37385649745
JOB: 10 state-driver replicas
COMMIT: ba09f11cf99ff3abefd7d63c490c97a74cdde7bd
SUPERSEDES: test-hub/findings/20261005-1912-state-driver-launcher-recovery-running.md

BASELINE_PROVEN: test-hub/findings/20261005-1908-state-driver-8of10-launcher-gap.md
SUCCESS_SIGNAL: FSM_MAIN_REACHED after an observed LAUNCHER_ANR and explicit recovery.
FAILURE_SIGNAL: FSM_TIMEOUT after an observed LAUNCHER_ANR and explicit recovery.
TEST_VALIDITY: a replica without LAUNCHER_ANR cannot test the recovery branch.

## Objetivo
Encerrar o RUNNING obsoleto e separar robustez geral da hipótese específica de recovery.

## Resultado
A matriz terminou cancelled no agregado. Seis jobs terminaram success e chegaram a FSM_MAIN_REACHED; quatro foram cancelled. Nos seis logs concluídos auditados não aparece Pixel Launcher isn't responding/LAUNCHER_ANR, portanto o branch de recovery não foi exercitado e seu SUCCESS_SIGNAL específico não ocorreu.

## Evidência decisiva
Jobs 112018141104, 112018141148, 112018141160, 112018141202, 112018141273 e 112018141342 emitiram FSM_MAIN_REACHED. Nenhum deles registrou LAUNCHER_ANR/Pixel Launcher isn't responding. Os outros quatro jobs foram cancelled.

## Consequência
Preservar a FSM como baseline parcial/provada para alcançar MAIN, mas manter launcher recovery como UNKNOWN/NOT_TESTED. Não repetir uma matriz ampla apenas para tentar provocar um evento raro; validar o branch de recovery com fixture/simulação controlada ou quando LAUNCHER_ANR reaparecer naturalmente.