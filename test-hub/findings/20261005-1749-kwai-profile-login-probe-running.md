# Profile/Login probe com 10 rotas em execução
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix with 10 profile/login probes
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: none

## Objetivo
Encontrar rota determinística da UI pós-onboarding até perfil/login sem repetir tentativas cegas de autologin.

## Resultado
Em execução no momento do registro.

## Evidência decisiva
Jobs ativos: profile-coordinate, me-coordinate, profile-deeplink, back-then-profile, inbox, inspect-profile, profile-text, profile-twice, discover e login-deeplink. Todos já passaram setup, checkout, vault e KVM e estão em Run profile probe.

## Consequência
Outros chats não devem iniciar outra matriz concorrente sobre a mesma camada enquanto este run estiver ativo. Após conclusão, registrar quais rotas realmente alcançaram login/perfil e usar apenas as promissoras no próximo autologin E2E.
