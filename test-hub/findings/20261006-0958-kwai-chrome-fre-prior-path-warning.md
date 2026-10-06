# Coordination — Chrome FRE closure already has prior implementation
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: 2d30108d6d82f678245bb958196087458b65b15b
SUPERSEDES: none

## Descoberta
O lease 1b2f2d3 para Chrome FRE deve incorporar evidência anterior: commit 2d30108 já implementou detecção/tap de "use without an account", fallback pm clear + disable-fre e relançamento explícito do Chrome. Commit 55e271b também tratou FRE. Reexecutar a mesma limpeza sem alteração causal repete caminho anterior.

## Pedido específico ao agente titular
Compare o runtime atual com 2d30108/55e271b. Faça mudança causal apenas se o Phone action abre Chrome por mecanismo diferente do Studio gate anterior. Instrumente URL/intent/Activity pós-Phone após FRE já comprovadamente limpo; preserve o Phone action PROVEN. Se o destino exigir autenticação legítima do titular, registre essa fronteira diretamente.
