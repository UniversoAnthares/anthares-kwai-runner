# Focused Start-now gate matrix launched after post-gate failure
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37383431568
JOB: 20-way Start gate matrix
COMMIT: a2ccee2ea0316de54632d17184811c113ffcc0d1
SUPERSEDES: test-hub/findings/20261005-2310-twenty-post-gate-failed.md

## Objetivo
Atacar a causa do run 37381528807: Start now reaparece porque o toque não é consumido de forma confiável.

## Resultado
37381528807 falhou; 17/20 jobs falharam e os 3 verdes tiveram EDITABLES=0/AUTH_CANDIDATES=0. Nova matriz testa 20 mecanismos exclusivamente no gate e mede XML_CHANGED, START_STILL e MAIN_NAV.

## Evidência decisiva
O hub registra repetição de GATE=START_NOW até NO_MAIN_NAV. parent-restart alcançou feed/nav, mas sem autenticação.

## Consequência
Promover apenas mecanismos com START_STILL=False e preferencialmente MAIN_NAV=True; depois compor vencedor com parent-restart/Profile.
