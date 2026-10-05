# TikTok 3/day is diagnostic mode, not production acceptance target
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 6255bf4189653155516947861ccd7288bcad52b7
SUPERSEDES: none

## Objetivo
Evitar que chats concorrentes confundam a cadência controlada do incidente de baixa distribuição com a meta de produção do sistema.

## Resultado
O finding 20261005-2257-tiktok-controlled-diagnostic-ready.md tornou 3/dia autoritativo para o experimento de distribuição e 3-6h entre observações. O controlador ainda contém daily_limit=100 e o projeto mantém a cadeia de produção de 100/dia como capacidade/meta separada. As duas regras pertencem a modos diferentes.

## Evidência decisiva
Finding 2257 declara explicitamente 3/dia como limite do diagnóstico enquanto o Worker ainda reporta remaining legado de 100/dia. O snapshot atual do Worker contém DAILY_LIMIT usado por queue-health e heartbeat daily_limit:100.

## Consequência
CHAT 3 deve manter 3/dia somente enquanto o diagnóstico de distribuição estiver ativo. Nenhum run a 3/dia prova a aceitação de throughput 100/dia; nenhum teste de 100/dia deve atropelar o experimento controlado. Findings futuros devem declarar MODE=DIAGNOSTIC ou MODE=PRODUCTION para eliminar ambiguidade.