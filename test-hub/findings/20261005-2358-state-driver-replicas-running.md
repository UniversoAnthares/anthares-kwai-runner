# Start-gate matrix invalid; state-driven replicas launched
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384859435
JOB: 10 state-driven replicas
COMMIT: edfe07291132b4daec51018a7b9fd07ddce93977
SUPERSEDES: test-hub/findings/20261005-2329-start-gate-focused-run.md

## Objetivo
Eliminar o erro metodológico da matriz Start-now: variantes recebiam estados iniciais diferentes e portanto não testavam a mesma hipótese.

## Resultado
37383431568 terminou failure. Jobs verdes observados chegaram com ALREADY_MAIN=1; vários vermelhos terminaram NO_START_GATE=1. Nenhuma técnica pode ser promovida causalmente. Implementado controlador state-driven que classifica PERMISSION, INTEREST, START, MAIN e OTHER em cada iteração, age conforme o estado real, valida persistência de START e usa relaunch se o gate persistir. Foram disparadas 10 réplicas independentes para medir robustez diante do estado inicial variável.

## Evidência decisiva
Hub 20261005-2350 registra a invalidação por estado inicial não determinístico. Logs do run 37383431568 confirmam ALREADY_MAIN nos verdes inspecionados e NO_START_GATE em rotas vermelhas.

## Consequência
Usar taxa FSM_MAIN_REACHED/10 como critério. Só após MAIN o controlador faz relaunch estabilizador, procura ll_profile e registra POST_PROFILE_UI/IDs. Não voltar a matrizes que ramificam antes de normalizar o estado.
