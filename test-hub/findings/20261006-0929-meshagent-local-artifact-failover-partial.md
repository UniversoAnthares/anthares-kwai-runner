# MeshAgent local artifact e failover
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: d87397b1f465a6c6, 60ce70998ffcc2c3, 7f358aea7ea84226, 1b7508f6fcdc6fda
COMMIT: none
SUPERSEDES: 20261006-0859-ai-commander-redundancy-winremote-meshcentral.md

## Objetivo
Fechar MeshAgent sem repetir o download anonimo que retornou HTTP 401.

## Resultado
O pacote npm MeshCentral contem MeshService64.exe. O binario reportou Windows 10 x64, ARCHID 4 e comandos run/connect/start/restart/install/fullinstall. O codigo do servidor confirma que o instalador Windows combina esse binario com configuracao contendo MeshName, MeshType, MeshID, ServerID, MeshServer e InstallFlags. Foi gerada configuracao local com IDs derivados do proprio servidor. O processo iniciou, porem ListDevices ainda retornou None.

Durante o teste AI Commander ficou OFFLINE. Remote Desktop Commander continuou mostrando DESKTOP-FTDK0HP Online, comprovando independencia de conectividade; execucao RDC esta pausada pela cota mensal.

## Evidencia
d87397b1f465a6c6 localizou os artefatos. 60ce70998ffcc2c3 validou o binario Windows. 7f358aea7ea84226 validou arquitetura e configuracao. 1b7508f6fcdc6fda iniciou o processo de conexao.

## Consequencia
Evitar GET anonimo /meshagents. Continuar por MeshService64.exe mais configuracao local. Quando houver executor disponivel, verificar processo MeshAgent, corrigir MeshServer se necessario e instalar como servico somente depois de o no aparecer em ListDevices. Preservar WinRemote MCP em loopback 8090 e MeshCentral Recovery em loopback 4432. Nao publicar portas administrativas.
