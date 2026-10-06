# Redundancia MeshCentral fechada operacionalmente
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: ea13b52131352864, 93e545f875088a26, 0b2e9e81ae5ad166, 4f0248ea1a4527de, 5030c50af4eee37d, 104464a3fb4b52c1, 7c2bcffda0d57ed2, 726b191aef3b0e68, 2ce2913f5d221cb8
COMMIT: none
SUPERSEDES: 20261006-0952-meshagent-service-installed-connection-partial.md

## Resultado
MeshAgent Windows x64 foi instalado pelo fluxo oficial autenticado de invite do MeshCentral. O download anônimo que retornava 401 foi abandonado. O instalador oficial incorporou as meshsettings corretas e executou -fullinstall com sucesso: desinstalou a instalação anterior, instalou serviço, atualizou firewall e iniciou o serviço.

O dispositivo apareceu no MeshCentral como DESKTOP-FTDK0HP, Windows 10 Pro 22H2/19045, agent id 4, conn=1. MeshCentral MCP autenticado continua expondo 58 ferramentas.

## Provas MCP
mesh_run_command: whoami + hostname + marcador MESH_PROVEN retornou AUTORIDADE NT\SISTEMA, DESKTOP-FTDK0HP e MESH_PROVEN.
mesh_file_write: criou mcp-proof.txt.
mesh_file_read: recuperou MESH_MCP_PROVEN_2026-10-06.
mesh_file_delete: removeu mcp-proof.txt.
mesh_list_processes: respondeu via MeshAgent.
mesh_list_devices: voltou a mostrar o nó após restart do Mesh Agent.
Mesh Agent foi reiniciado e permaneceu Running/Automatic.
MeshCentral Recovery foi parado/iniciado e voltou a escutar 127.0.0.1:4432; o agente reapareceu depois, comprovando reconexão após restart do servidor.

## Segurança
Portas administrativas permanecem em loopback. O agente oficial usa o serviço LocalSystem. Arquivos temporários de invite contendo URL de instalação foram removidos após a instalação. Nenhum token foi registrado neste finding.

## Limitação
git status via MeshAgent chegou ao repositório, mas o processo roda como SYSTEM e o Git recusou o repositório por dubious ownership. Isso não é falha do transporte MeshCentral. A prova Git deve ser feita por configuração segura de safe.directory temporária ou outro contexto somente-leitura, sem alterar o repositório permanentemente.

## ChatGPT
A instalação local dos MCPs está pronta. A integração direta ao ChatGPT permanece dependente do mecanismo de MCP remoto/Developer Mode disponível na conta. A documentação atual da OpenAI diz que ChatGPT não conecta diretamente a MCP local e orienta Secure MCP Tunnel; full MCP/write está disponível em Business/Enterprise/Edu, enquanto Pro pode conectar MCP com permissões de leitura/fetch em Developer Mode.

## Próximo passo
Se a conta tiver Developer Mode e suporte ao MCP remoto, configurar um Secure MCP Tunnel para o endpoint do MCP sem publicar 8090/4432. Em seguida criar o app customizado em Settings > Apps > Create, informar endpoint/metadados, Scan Tools e testar. Não expor as portas locais diretamente.
