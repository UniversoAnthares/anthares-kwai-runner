# Lease architecture meshagent service closure
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Concluir MeshAgent como serviço separado e provar redundancias administrativas.

## BASELINE_PROVEN
MeshCentral e MeshCentral MCP autenticado funcionam; WinRemote MCP funciona em loopback; MeshService64.exe Windows x64 e configuracao local foram validados.

## FAILED_AVOIDED
Evitar download anonimo /meshagents que retorna 401. Evitar MeshAgent em modo console run, associado a quedas temporarias do AI Commander. Usar instalacao como servico separado.

## SUCCESS_SIGNAL
Servico Mesh Agent instalado e running; dispositivo aparece no MeshCentral; comando remoto basico funciona; WinRemote e MeshCentral sobrevivem a reinicio de seus proprios servicos.

## FAILURE_SIGNAL
Servico nao instala/inicia ou agente nao aparece apos configuracao valida.

## TEST_VALIDITY
AI Commander deve permanecer online durante as mutacoes; queda do executor invalida a prova em curso.

Expira em 30 minutos.
