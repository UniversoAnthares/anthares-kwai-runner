# Focused login UI inspection after RC3
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380670886
JOB: inspect
COMMIT: 452cdf5cf0358a72f984321ac39e28a2293babbe
SUPERSEDES: none

## Objetivo
Descobrir exatamente qual controle/tela abre o formulário de login, sem usar credenciais e sem repetir o E2E que terminou RC=3.

## Resultado
Instrumentação criada para registrar texto, content-desc, resource-id, classe, clickable/editable e bounds em cada transição após adaptive + restart-after-nav + Profile semântico. Run disparado.

## Evidência decisiva
O teste anterior 37379608085 terminou RC=3 antes de qualquer preenchimento. Este probe remove credenciais da equação e inspeciona a árvore UI que faltava.

## Consequência
Só alterar os seletores do autologin depois deste resultado. Se um campo editável/controle for identificado, fazer uma única nova aceitação credenciada com seletor baseado em evidência.
