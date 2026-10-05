# Twenty-way post-Start-now route matrix
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381528807
JOB: 20-route matrix
COMMIT: 7d2a1eb40083d44219081ca309fd872ba800ad3f
SUPERSEDES: test-hub/findings/20261005-2255-start-now-gate-blocked-profile.md

## Objetivo
Tratar explicitamente o gate Start now comprovado e explorar em paralelo rotas distintas até Profile/auth.

## Resultado
Criada matriz fail-fast=false com 20 variantes: parent-now, waits 5/15/30, restart, restart+wait, twice, back, home/inbox/discover->profile, resource variants, start/restart variants, activity dump, menu, scroll up/down e coordinate. Todas atravessam os gates conhecidos incluindo tiny_discovery_left_operation_btn antes da divergência.

## Evidência decisiva
Run 37381528807 criado com matriz de 20 jobs. O GitHub Actions suporta matriz e fail-fast=false para preservar resultados independentes.

## Consequência
Comparar EDITABLES, AUTH_CANDIDATES e FINAL_UI de todos os jobs; promover apenas a rota com mudança inequívoca para Profile/login. Não repetir a travessia que ignorava Start now.
