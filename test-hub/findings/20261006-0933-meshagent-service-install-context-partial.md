# MeshAgent service install context dependency
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: 2aa263c8da80cab4
COMMIT: none
SUPERSEDES: 20261006-0929-meshagent-local-artifact-failover-partial.md

## Objetivo
Instalar MeshAgent como servico sem usar modo console.

## Resultado
A tentativa elevada de MeshService64.exe -fullinstall executou como SYSTEM e retornou: Checking for previous installation [NONE], Installing service [ERROR] fs.mkdirSync(): Unable to create dir: undefined\Mesh Agent. A causa e dependencia de perfil/diretorio na etapa fullinstall sob SYSTEM. O caminho causal seguinte e MeshService64.exe -install a partir do diretorio preparado, que evita a copia de fullinstall.

A tentativa de criar uma tarefa SYSTEM pelo usuario comum retornou Acesso negado. O canal elevated ficou temporariamente serializado por uma chamada ainda marcada em execucao, enquanto jobs comuns seguem funcionando.

## Consequencia
Nao repetir -fullinstall sob SYSTEM. Executar -install elevado a partir de C:\Users\Lucas\AntharesWork\mesh-agent-install quando o slot elevated liberar. Evitar modo console run.
