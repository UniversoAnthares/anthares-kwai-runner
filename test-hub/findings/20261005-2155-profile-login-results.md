# Profile/login matrix results
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix of 10
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: test-hub/findings/20261005-2150-profile-login-probes-running.md

## Objetivo
Partir do onboarding e localizar uma rota determinística até Profile/login.

## Resultado
9 jobs concluíram success no harness; me-coordinate falhou por erro de preparação do Android Emulator (ZipFile/ADB), portanto não é evidência contra a hipótese. profile-text e back-then-profile chegaram à navegação Home/Discover/Inbox/Profile, mas com "Can't connect to server" e "Resource downloading". profile-coordinate, profile-twice, discover, login-deeplink e inspect-profile ficaram no onboarding. profile-deeplink e inbox terminaram com "Pixel Launcher isn't responding".

## Evidência decisiva
profile-text/back-then-profile: "can't connect to server ... home discover inbox profile ... resource downloading".
me-coordinate: "Android Emulator: Error on ZipFile unknown archive" e ADB connection refused.
profile-deeplink/inbox: "Pixel Launcher isn't responding".

## Consequência
O gargalo mudou: não é mais apenas encontrar coordenada de Profile. Precisamos estabilizar a travessia do onboarding e aguardar/validar os recursos/rede do Kwai antes de tentar Profile. Não classificar me-coordinate como FAILED funcional.
