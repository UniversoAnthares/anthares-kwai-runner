# Second-stage profile/login probe matrix
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix of 10
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: none

## Objetivo
Partir da travessia adaptive comprovada e descobrir a rota determinística da interface principal para Profile/login.

## Resultado
Dez estratégias disparadas em paralelo: profile-text, profile-coordinate, me-coordinate, back-then-profile, profile-twice, profile-deeplink, login-deeplink, inbox, discover e inspect-profile.

## Evidência decisiva
Run 37378176856 criado e atualmente queued.

## Consequência
Não escolher uma rota de login antes de comparar as evidências desta matriz. O próximo fluxo deve incorporar a rota que realmente expuser login/conta.
