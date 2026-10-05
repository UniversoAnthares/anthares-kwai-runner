# Network gate cleared after adaptive onboarding
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378882974
JOB: 111995283098
COMMIT: f9636b8c8e4f3ae180c7613bf02a6cf1666d5a1b
SUPERSEDES: test-hub/findings/20261005-2202-network-gate-v2-running.md

## Objetivo
Determinar se "Can't connect to server / Resource downloading" era um bloqueio persistente após o onboarding adaptive.

## Resultado
O probe concluiu success. Após adaptive, a UI estabilizou na navegação principal e exibiu conteúdo real de feed/perfil ("Jehad Aljondy", Follow, métricas, Home/Discover/Inbox/Profile). Em cinco checkpoints não apareceu Resource downloading e RESOURCE_PROGRESS foi NONE.

## Evidência decisiva
UI_CHECK_0..4 mantiveram conteúdo real + barra principal. RESOURCE_PROGRESS_0..4=NONE. O Android resolveu www.kwai.com, m.kwai.com, api.kwai.com e www.google.com. ICMP teve 100% loss, inclusive Google, portanto ping não é critério válido de conectividade neste ambiente.

## Consequência
O gate de recursos não é permanente e não deve mais bloquear a sequência. Preservar adaptive e avançar para Profile/login/autologin sobre o estado estabilizado. Não usar ping/ICMP como teste de saúde. Não repetir a matriz ampla de Profile.
