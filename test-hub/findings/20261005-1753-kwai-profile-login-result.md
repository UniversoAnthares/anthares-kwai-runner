# Profile/Login probe: barra principal alcançada; falha global não invalida hipótese
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix profile/login
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: test-hub/findings/20261005-1749-kwai-profile-login-probe-running.md

## Objetivo
Encontrar uma rota determinística da UI pós-onboarding até Profile/Login.

## Resultado
O run terminou failure porque somente me-coordinate falhou durante preparação/boot do Android SDK: "Error on ZipFile unknown archive" e conexão ADB recusada. Isso é falha do harness/ambiente e NÃO testa a hipótese me-coordinate.

Nove outros jobs executaram. back-then-profile e profile-text chegaram a uma UI com barra principal textual: Home / Discover / Inbox / Profile. profile-coordinate, inspect-profile, profile-twice, discover e login-deeplink permaneceram no onboarding (Choose like or dislike... 1/N). profile-deeplink e inbox terminaram com instabilidade do Pixel Launcher.

## Evidência decisiva
back-then-profile: PROFILE_UI contém "home discover inbox profile" e mensagem de resource downloading.
profile-text: PROFILE_UI contém "home discover inbox profile" e a mesma mensagem.
me-coordinate: Android Emulator SDK preparation falhou antes do probe; não classificar a estratégia como FAILED.
Outras rotas citadas exibiram onboarding ou launcher instável.

## Consequência
Não repetir coordenadas cegas como primeira opção. A próxima implementação deve atravessar onboarding de forma determinística, detectar a barra principal e acionar Profile semanticamente (texto/resource-id), então localizar a entrada de login e executar um único autologin E2E credenciado. Não multiplicar tentativas credenciadas simultâneas.
