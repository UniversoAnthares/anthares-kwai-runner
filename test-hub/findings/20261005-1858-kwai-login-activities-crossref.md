# Cross-reference identifica activities concretas de login no APK
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37384780073
JOB: inspect
COMMIT: b504dc0e240fafbb00aaee65840a216478016613
SUPERSEDES: none

## Objetivo
Cruzar recursos de login encontrados no APK com classes/componentes concretos para evitar dependência da rota instável Profile/DFM.

## Resultado
A análise estática encontrou classes concretas do fluxo tiny de autenticação: com.yxcorp.gifshow.tiny.login.activity.TinyLoginActivity, TinyUserInfoActivity, TinyGoogleSSOActivity e TinyLoginPluginImpl. Também encontrou com.yxcorp.login.userlogin.activity.AutoLoginActivity/AutoLogoutActivity e recursos auth_token_login_button, tiny_login_content_container e tiny_google_login_platform_item.

## Evidência decisiva
DEX CLASS CANDIDATES contém TinyLoginActivity, TinyUserInfoActivity, TinyGoogleSSOActivity, TinyLoginPluginImpl e AutoLoginActivity; strings incluem LOGIN_PAGE_NEW, LOGIN_OR_SIGNUP, authTokenLogin e auth_token_login_button.

## Consequência
A próxima bateria deve testar diretamente, sem credenciais, se essas activities são declaradas/exportadas/iniciáveis e qual UI produzem. Não insistir em Profile/DFM para descobrir o formulário. Só depois de uma surface de login comprovada fazer um único E2E credenciado.
