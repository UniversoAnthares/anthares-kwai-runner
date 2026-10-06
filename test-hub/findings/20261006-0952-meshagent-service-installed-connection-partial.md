# MeshAgent service installed; connection diagnosis remaining
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: 207d8c63d95f2866, a18df96f1706f86a, 45737309adf469c9, b8a28a8f3af054b8
COMMIT: none
SUPERSEDES: 20261006-0933-meshagent-service-install-context-partial.md

## Resultado
MeshService64.exe -install executado elevado com sucesso: service install DONE, firewall rules DONE, service start OK. Windows confirma Mesh Agent Running Automatic como LocalSystem. Isso encerra o bloqueio de instalacao.

MeshCentral Recovery continua ouvindo em 127.0.0.1:4432. MeshCentral MCP continua autenticando e expondo 58 tools. Quatro consultas mesh_list_devices apos instalacao/restarts retornaram nodes vazio. O agente service permanece Running, mas sem conexao TCP observavel ao servidor.

Foi corrigido ServerID: a primeira configuracao usava SHA384 do certificado completo; o codigo MeshCentral usa getPublicKeyHash, e o valor foi substituido pelo SHA384 da public key. Tambem foi testado MeshServer localhost/127.0.0.1. O no ainda nao registrou.

## Evidencia
Instalacao elevada: Checking previous [NONE], Installing service [DONE], firewall [DONE], Starting service [OK].
Windows: Mesh Agent Running Automatic, PathName C:\Users\Lucas\AntharesWork\mesh-agent-install\MeshService64.exe, StartName LocalSystem.
Jobs MCP listdevices acima: Connected to MeshCentral, TOOLS 58, nodes {}.

## Consequencia
MESHCENTRAL_SERVICE_INSTALL=PROVEN. MESHCENTRAL_MCP_CONTROL_PLANE=PROVEN. MESHCENTRAL_REMOTE_EXEC ainda PARTIAL ate o agente registrar. Preservar o servico instalado. Proxima investigacao deve focar no formato/embedding de meshsettings usado pelo MeshService64 instalado: o servico parece nao consumir meshagent.msh externo, pois inicia sem socket. Evitar reinstalar e evitar modo console.
