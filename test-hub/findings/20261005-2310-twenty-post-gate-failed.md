# Twenty-way post-gate matrix: mixed harness states, no login
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381528807
JOB: 20-route matrix
COMMIT: 7d2a1eb40083d44219081ca309fd872ba800ad3f
SUPERSEDES: test-hub/findings/20261005-2300-twenty-post-gate-routes-running.md

## Objetivo
Atravessar Start now e comparar 20 rotas para Profile/login.

## Resultado
17 jobs falharam; 3 concluíram o harness (parent-twice, parent-dump-activities, parent-restart), mas nenhum encontrou login: EDITABLES=0 e AUTH_CANDIDATES=0. parent-restart foi o melhor estado: feed real + nav, porém ainda Resource downloading. Diversos jobs repetiram GATE=START_NOW até esgotar 30 iterações e terminar RESULT=NO_MAIN_NAV. Isso prova que detectar/tocar o botão não garante que o gate seja consumido; o script precisa validar transição após o toque e aplicar alternativas ao próprio Start now.

## Evidência decisiva
parent-restart: feed real + Home/Discover/Inbox/Profile + Resource downloading; EDITABLES=0; AUTH_CANDIDATES=0.
parent-twice/dump-activities: Can't connect to server + Resource downloading; zero auth/editables.
parent-now e parent-discover-profile: GATE=START_NOW repetido muitas vezes -> RESULT=NO_MAIN_NAV -> exit 20.

## Consequência
Não repetir matriz que assume sucesso do toque Start now. Próximo harness deve testar mecanismos diferentes para consumir esse gate (node bounds, parent bounds, coordinate center, ENTER/DPAD, accessibility click, restart before/after, wait/download), verificando mudança real de XML a cada tentativa. Só depois divergir em Profile.
