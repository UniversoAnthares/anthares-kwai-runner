# Second-stage profile/login probe matrix completed
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix of 10
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: test-hub/findings/20261005-2150-profile-login-probes-running.md

## Objetivo
Partir da travessia adaptive comprovada e descobrir a rota determinística da interface principal para Profile/login.

## Resultado
Dez estratégias executadas em paralelo. 9 completaram success no harness; 1 falhou (me-coordinate, exit code 1). Artefatos gerados para os 9 sucessos contêm XMLs de UI (stage-*, before-profile, after-{mode}) e screenshots.

Estratégias success:
- profile-text: tap em node com texto "profile"
- profile-coordinate: tap coordenada (960,2200)
- back-then-profile: keyevent BACK + tap (960,2200)
- profile-twice: tap duplo em (960,2200)
- profile-deeplink: am start kwai://profile
- login-deeplink: am start kwai://login
- inbox: tap área inbox (800,2200)
- discover: tap área discover (300,2200)
- inspect-profile: dumpsys activity activities

Falha:
- me-coordinate: tap (970,2140) — crashou o harness (exit 1), sem artefato.

## Evidência decisiva
Run 37378176856 concluído em 4m14s. 9 artefatos produzidos (68KB–1MB). me-coordinate falhou com "The process '/usr/bin/sh' failed with exit code 1" e "No files were found with the provided path" para upload de artefato. As 9 estratégias success não travaram o harness, mas o conteúdo de UI (se expuseram login/conta) está nos XMLs/screenshots dos artefatos — requer download autenticado para inspeção detalhada.

## Consequência
Não é possível declarar uma rota vencedora sem inspecionar os XMLs after-{mode} para confirmar qual efetivamente expôs tela de login/conta. Próximo passo: disparar teste focalizado nas estratégias mais promissoras (profile-text, back-then-profile, login-deeplink, profile-deeplink) com evidência de log acessível (ex: imprimir PROFILE_UI no log do step, não só em artefato) para comparar e escolher a rota que de fato chega ao login.