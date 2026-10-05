# Corrected ten-way onboarding matrix
STATUS: RUNNING
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37377433515
JOB: matrix of 10
COMMIT: bdda1fe034d98e3dc0869c98958995b6ca8cd381
SUPERSEDES: test-hub/findings/20261005-2103-ten-probes-invalid-heredoc.md

## Objetivo
Executar dez estratégias reais e independentes: baseline, permission, back, swipe, tap, activity, intent, settings, adaptive e inspect.

## Resultado
Disparado com fail-fast=false. A lógica foi movida para kwai_onboarding_probe.py, eliminando o erro de boundary/heredoc.

## Evidência decisiva
GitHub criou os dez jobs separados no run 37377433515.

## Consequência
Consultar o resultado deste run antes de escolher a estratégia de onboarding.
