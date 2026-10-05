# Composed profile flow and login-control discovery
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380001963
JOB: 111999232625
COMMIT: 95fa249de6ebab11a162211b483b64b8bc42cc2c
SUPERSEDES: none

## Objetivo
Compor onboarding adaptativo + restart comprovado + abertura de Profile e localizar o controle de autenticação.

## Resultado
O fluxo composto concluiu success e estabilizou feed real. Porém o clique em Profile não mudou a UI: PROFILE_PAGE_UI continuou sendo o feed/nav e exibiu Resource downloading. Em teste paralelo de descoberta, a árvore revelou o controle clicável real com resource-id com.kwai.video:id/ll_profile, mas após a tentativa STATE=PROFILE ainda houve AUTH_CANDIDATES=0 e LOGIN_FORM_FOUND=0. O autologin paralelo continuou falhando RC=3.

## Evidência decisiva
Run 37380001963: STABLE_UI contém conteúdo real + follow + home/discover/inbox/profile; PROFILE_PAGE_UI permanece no mesmo estado + resource downloading.
Run 37379937689: NODE com.kwai.video:id/ll_profile LinearLayout clickable=true; AUTH_CANDIDATES=0; LOGIN_FORM_FOUND=0; exit 21.
Run 37379608085: AUTOLOGIN_FAILED_RC=3.

## Consequência
Não procurar campos de login diretamente nem clicar no TextView Profile. O próximo fluxo deve clicar especificamente o pai clicável resource-id com.kwai.video:id/ll_profile, aguardar Resource downloading desaparecer/estabilizar e capturar cada transição antes de executar autologin.
