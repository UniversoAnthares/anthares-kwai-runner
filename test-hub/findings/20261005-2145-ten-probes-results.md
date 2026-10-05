# Corrected ten-way onboarding matrix results
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37377433515
JOB: matrix of 10
COMMIT: bdda1fe034d98e3dc0869c98958995b6ca8cd381
SUPERSEDES: test-hub/findings/20261005-2139-ten-probes-script-rerun.md

## Objetivo
Comparar dez estratégias reais para atravessar a primeira execução do Kwai no Android remoto.

## Resultado
Os dez jobs concluíram success no harness. Baseline, swipe, activity, tap, permission, back e settings permaneceram na tela "Choose like or dislike to let us know you better". Intent e inspect chegaram ao shell principal com Home/Discover/Inbox/Profile, mas exibiram "Can't connect to server". A estratégia adaptive atravessou o onboarding e chegou a uma interface real de feed, com Follow e navegação Home/Discover/Inbox/Profile.

## Evidência decisiva
adaptive: UI continha "follow ... home discover inbox profile".
baseline e variantes estáticas: UI continha "choose like or dislike to let us know you better".
intent/inspect: UI continha "can't connect to server ... home discover inbox profile".

## Consequência
Usar adaptive como base do próximo fluxo. Não investir novamente em back/swipe/tap fixos ou mera concessão de permissão como solução isolada. Próximo teste deve partir do adaptive e navegar Profile -> login, coletando XML/evidência em cada transição.
