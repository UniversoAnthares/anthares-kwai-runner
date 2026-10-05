# State driver result: 8/10 reached MAIN; Profile blocked by dynamic resource
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384859435
JOB: 10 state-driven replicas
COMMIT: edfe07291132b4daec51018a7b9fd07ddce93977
SUPERSEDES: test-hub/findings/20261005-2358-state-driver-replicas-running.md

## Objetivo
Normalizar o onboarding por estado real e medir robustez até MAIN/Profile.

## Resultado
8 de 10 réplicas concluíram success e exibiram FSM_MAIN_REACHED. Uma falhou e uma foi cancelada; ambas ficaram presas em dialog do sistema "Pixel Launcher isn't responding", classificado como OTHER até FSM_TIMEOUT. Nas réplicas válidas, PROFILE_PARENT=True, mas após clicar Profile a UI permaneceu no feed e abriu o overlay de módulo dinâmico: Resource downloading / You'll have access to all the features when it's done / btn_cancel. Portanto a FSM corrige o onboarding; o bloqueador causal atual é o carregamento do módulo dinâmico após Profile. O erro restante da FSM é não tratar ANR do Pixel Launcher como estado recuperável.

## Evidência decisiva
Jobs 1,2,3,4,5,7,9,10: FSM_MAIN_REACHED. Exemplos percorrem INTEREST 1/N -> START -> MAIN.
Jobs 6 e 8: STATE=OTHER UI="pixel launcher isn't responding close app wait" repetido até FSM_TIMEOUT.
Após MAIN: PROFILE_PARENT=True e POST_PROFILE_IDS inclui fl_tiny_total_dfm_window, progress_bar, tv_loading_title, tv_loading_content, btn_cancel; texto Resource downloading.

## Consequência
Preservar a FSM e adicionar recuperação explícita do ANR do launcher. Não voltar a testar onboarding por matrizes cegas. Próximo experimento causal deve partir de MAIN comprovado e investigar exclusivamente o módulo dinâmico/DFM acionado por ll_profile, com precondição MAIN obrigatória; jobs que não atingirem MAIN são INVALID/NOT_TESTED para DFM.
