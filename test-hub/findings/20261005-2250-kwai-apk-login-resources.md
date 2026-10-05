# APK component matrix exposes packaged login resources
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37383460988
JOB: matrix
COMMIT: 640338531eecdd4487c12787f7efcabd3e6ca7bd
SUPERSEDES: none

## Objetivo
Inspecionar estaticamente os APKs/splits validados para descobrir componentes e recursos ligados a Profile e autenticação sem depender da travessia instável do onboarding.

## Resultado
A matriz terminou success e encontrou recursos de login empacotados no aplicativo, incluindo tiny_google_login_platform_item, tiny_login_close, tiny_login_content_container, tiny_login_label, tiny_login_progress_bar, tiny_login_sub_label, tiny_login_tv_protocol, auth_token_login_button, auth_token_login_desc e strings de Authorized Login/Login autorizado. Também confirmou Profile e ll_profile.

## Evidência decisiva
Job login-strings do run 37383460988 imprimiu os IDs/strings de login acima e terminou COMPONENT_PROBE_DONE=login-strings. Job profile-strings imprimiu Profile e ll_profile.

## Consequência
Usar esses IDs concretos como alvos no próximo experimento. Evitar nova busca genérica por texto/coordinate. Investigar no APK onde tiny_login_content_container/tiny_google_login_platform_item são referenciados e, se houver activity/fragment/deeplink correspondente, iniciar diretamente essa superfície no Android real e validar EditText/controle de autenticação.
