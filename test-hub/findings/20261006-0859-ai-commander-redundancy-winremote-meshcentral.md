# Redundâncias AI Commander: WinRemote MCP e MeshCentral MCP
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: AI Commander jobs 37083cd25de6174e, 51151cea1971b8a6, d05c94afeefd3c2d, 7d322b735373c0b9
COMMIT: none
SUPERSEDES: none

## Objetivo
Criar caminhos independentes de administração para aic-lucas-pc por WinRemote MCP e MeshCentral/MeshCentral MCP, preservando AI Commander e Remote Desktop Commander.

## Resultado
WinRemote MCP 0.4.24 foi instalado no Windows e executado como tarefa agendada independente, bind somente em 127.0.0.1:8090, tiers 1/2/3 e 45 ferramentas. MeshCentral 1.2.5 e meshcentral-mcp foram instalados. Uma instância limpa do MeshCentral em 127.0.0.1:4432 autenticou com o MCP e o MCP criou/listou o grupo aic-lucas-pc. A instalação do MeshAgent ainda não fechou: download direto sem sessão autenticada retornou HTTP 401. Integração MCP de escrita diretamente no ChatGPT também permanece bloqueada pela disponibilidade atual do produto/conta; full MCP write é documentado pela OpenAI para Business/Enterprise/Edu.

## Evidência decisiva
- WinRemote job 37083cd25de6174e: Shell retornou desktop-ftdk0hp\\lucas e DESKTOP-FTDK0HP; FileWrite/FileRead funcionaram; ListProcesses funcionou; git status em C:\\Users\\Lucas\\AntharesWork\\anthares-kwai-runner funcionou; Snapshot enumerou a sessão gráfica; arquivo temporário foi removido.
- WinRemote job 51151cea1971b8a6: após substituir o servidor temporário pela tarefa agendada Anthares WinRemote MCP, chamada MCP Shell retornou desktop-ftdk0hp\\lucas e DESKTOP-FTDK0HP.
- MeshCentral MCP job d05c94afeefd3c2d: Connected to MeshCentral, 58 tools.
- MeshCentral MCP job 7d322b735373c0b9: mesh_create_group result=ok e mesh_list_groups confirmou aic-lucas-pc.
- MeshAgent job 707a118a76052069: GET /meshagents sem autenticação retornou HTTP 401.

## Consequência
Preservar a tarefa agendada Anthares WinRemote MCP e a instância limpa meshcentral-proof. Não expor 8090 ou 4432 diretamente à Internet. Próximo passo MeshCentral: obter o agente Windows x64 por fluxo autenticado e provar mesh_run_command/arquivos/processos via MCP. Para ChatGPT, usar Secure MCP Tunnel somente em produto/plano que aceite custom MCP; não substituir isso por porta pública sem autenticação.
