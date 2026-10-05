# Dois discoveries falham antes de Profile por gates distintos
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380678547 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380757409
JOB: 112001554525 ; 112001820706
COMMIT: ac7cc99ec069d2da218519af6e0537beb17d098e ; 1c47615e86fd37648bea780620eabb7d2c119929
SUPERSEDES: none

## Objetivo
Reexecutar descoberta de controle de login após tornar o fluxo consciente do módulo dinâmico.

## Resultado
Nenhum run chegou a testar Profile/login. 37380757409 terminou em NO_MAIN_NAV na tela final do onboarding: "You're all set. Hope you enjoy the Kwai!" com botão clicável "Start now" (resource-id tiny_discovery_left_operation_btn). 37380678547 terminou em NO_MAIN_NAV porque apareceu diálogo do sistema "Pixel Launcher isn't responding", com botões Close app/Wait.

## Evidência decisiva
37380757409: tiny_discovery_install_dfm_title + tiny_discovery_left_operation_btn text="start now", exit 20.
37380678547: android:id/alertTitle="pixel launcher isn't responding", android:id/aerr_close e android:id/aerr_wait, exit 20.

## Consequência
Não repetir o discovery atual sem causal change. O traverser deve clicar semanticamente Start now e recuperar diálogos de launcher antes de declarar NO_MAIN_NAV. Esses gates podem ser testados em paralelo sem credenciais. Profile/login permanece não refutado.
