# Profile/login matrix did not expose login and one job had harness failure
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix of 10
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: test-hub/findings/20261005-2150-profile-login-probes-running.md

## Objetivo
Comparar dez rotas de segunda etapa para sair do fluxo adaptive e alcançar Profile/login.

## Resultado
O run terminou failure. Nenhuma das evidências textuais coletadas comprovou tela de login ou EditText. profile-text e back-then-profile chegaram ao shell Home/Discover/Inbox/Profile, porém com "Can't connect to server" e "resource downloading". profile-coordinate, profile-twice, inspect-profile, discover e login-deeplink permaneceram no onboarding. profile-deeplink e inbox terminaram com "Pixel Launcher isn't responding". me-coordinate falhou antes do teste por erro de preparação do Android Emulator/ADB e portanto não constitui evidência contra essa hipótese.

## Evidência decisiva
profile-text e back-then-profile: PROFILE_UI continha "can't connect to server ... home discover inbox profile ... resource downloading". profile-coordinate/profile-twice/inspect-profile/login-deeplink: "choose like or dislike...". profile-deeplink/inbox: "pixel launcher isn't responding". me-coordinate: "Error on ZipFile unknown archive" seguido de connection refused antes da execução da hipótese.

## Consequência
Não tratar os jobs verdes como sucesso de login: o harness aceitava execução sem validar o objetivo. Não repetir as rotas que permaneceram no onboarding ou produziram launcher travado sem alteração causal. O próximo teste deve focar a condição observada em profile-text/back-then-profile: aguardar explicitamente a conclusão de "resource downloading" e só então tocar Profile, coletando XML/screenshot antes e depois. me-coordinate permanece inconclusivo porque seu harness falhou.
