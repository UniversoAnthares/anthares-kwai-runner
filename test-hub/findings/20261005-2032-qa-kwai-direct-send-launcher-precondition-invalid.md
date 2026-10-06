# Kwai direct SEND rerun did not test SEND because launcher recovery failed
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37392541208
JOB: 112040761050
COMMIT: 91dd60e0ebbfc94404c323bc74271659dd17c6e5
SUPERSEDES: none

BASELINE_PROVEN: direct SEND is a distinct exported UriRouterActivity path; ffmpeg fixture defect was repaired before this run.
FAILED_AVOIDED: missing-ffmpeg harness defect was removed.
SUCCESS_SIGNAL: FSM_MAIN_REACHED followed by exact ACTION_SEND handoff and composer/media UI evidence.
FAILURE_SIGNAL: valid MAIN then SEND resolves but does not reach composer/media UI.
TEST_VALIDITY: SEND hypothesis is valid only after FSM_MAIN_REACHED.

## Resultado
O rerun não testou ACTION_SEND. O FSM ficou em LAUNCHER_ANR de STATE 13 a 44 e terminou FSM_TIMEOUT antes do handoff. Logo a conclusão do job failure não conta contra a hipótese SEND.

## Evidência decisiva
Job 112040761050 repetiu STATE=LAUNCHER_ANR com Pixel Launcher isn't responding até FSM_TIMEOUT; não ocorreu FSM_MAIN_REACHED nem evidência posterior de SEND.

## Consequência
Classificar 37392541208 como harness/precondition failure. Não declarar ACTION_SEND falho por este run. O gargalo reaberto é exatamente o recovery de Launcher que permanecia UNKNOWN; o próximo teste só pode reutilizar SEND depois de um MAIN válido ou de uma correção causal do recovery.