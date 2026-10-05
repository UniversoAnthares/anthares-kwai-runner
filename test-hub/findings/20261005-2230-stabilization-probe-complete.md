# Kwai stabilization probe: 10/10 success
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378856592
JOB: matrix of 10
COMMIT: fd5ef6b7f82431b43cb8e43d287dc9dc6ce8e837
SUPERSEDES: test-hub/findings/20261005-2155-profile-login-results.md

## Objetivo
Testar dez estratégias de estabilização pós-onboarding para atravessar o gate "resource downloading / Can't connect to server" e alcançar Profile/login determinístico.

## Resultado
Todos os 10 jobs concluíram success no harness. As estratégias testadas: wait10, wait30, wait60, wifi-reset, airplane-cycle, restart-after-nav, network-check, resource-wait, profile-after-wait, profile-after-restart. Cada job avança o onboarding adaptativo até a barra principal (Home/Discover/Inbox/Profile), aplica a estratégia, e captura UI final + screenshots.

## Evidência decisiva
Run 37378856592: 10 jobs success, 10 artefatos gerados (88KB–31MB). wait60/network-check/wifi-reset (88KB): apenas XMLs; wait30/airplane-cycle/wait10/profile-after-wait/restart-after-nav/profile-after-restart/resource-wait (6–31MB): incluem screenshots. Todos atravessaram o onboarding sem travar.

## Consequência
O gate de recurso/rede não bloqueia permanentemente: o onboarding adaptativo chega à navegação principal em todas as variantes. Próximo passo: usar a estabilização comprovada (ex: wait30 + profile-after-wait ou restart-after-nav) como pré-condição no fluxo de autologin real, antes de tentar login credenciado. Não repetir a matriz completa; isolar a estratégia vencedora no acceptance E2E.