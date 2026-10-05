# State driver proves normalized onboarding; aggregate run red from one launcher failure
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384859435
JOB: 10 state-driven replicas
COMMIT: edfe07291132b4daec51018a7b9fd07ddce93977
SUPERSEDES: test-hub/findings/20261005-2358-state-driver-replicas-running.md

## Objetivo
Normalizar estados variáveis de onboarding antes de Profile.

## Resultado
O run agregado terminou failure, mas 8 réplicas concluíram success e mostram FSM_MAIN_REACHED + PROFILE_PARENT=True. Uma réplica falhou por Pixel Launcher isn't responding até FSM_TIMEOUT; uma foi cancelled. Nas réplicas válidas inspecionadas, INTEREST -> START -> MAIN ocorreu deterministicamente. Após restart + ll_profile, a UI ainda mostrou feed/nav + Resource downloading em vez de login.

## Evidência decisiva
Jobs 4,2,3,9,7,1,10,5 success. Exemplos: réplica 4 percorreu INTEREST 1/9..9/9, START, MAIN, FSM_MAIN_REACHED, PROFILE_PARENT=True. Réplica 8 ficou em OTHER='pixel launcher isn't responding' e terminou exit 20. Pós-Profile das válidas: feed + Home/Discover/Inbox/Profile + Resource downloading.

## Consequência
Não classificar a FSM como hipótese falha por causa do status agregado. Onboarding state-driven está parcialmente comprovado e deve ser preservado. Próximo gargalo é o módulo/rota de Profile após MAIN, apoiado pela análise estática PROVEN de TinyLoginActivity/TinyUserInfoActivity/TinyLoginPluginImpl. Não repetir matrizes de onboarding.
