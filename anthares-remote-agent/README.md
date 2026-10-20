# Anthares Remote Agent

Anthares Remote é o canal canônico de administração remota do Windows do projeto Anthares.

## Runtime canônico no Windows

Dispositivo: `DESKTOP-FTDK0HP`.

Existe **um único executor canônico**:

- tarefa: `Anthares Remote Agent SYSTEM`;
- identidade: `SYSTEM`, `Highest`;
- sessão: `0`;
- instalação executável: `C:\ProgramData\AntharesRemoteAgent`;
- trabalho/logs/jobs/estado: `D:\AntharsWork`;
- supervisor: `windows/run-agent-system-supervisor.ps1`;
- recuperação: `windows/recovery-watchdog-loop.ps1` -> `windows/recovery-watchdog.ps1`;
- processo: um único `anthares-remote-agent-v4-c8.exe` com transportes simultâneos.

`D:\AntharsWork\AntharesRemoteAgent` pode existir como staging histórico, mas não é raiz válida para tarefas ou supervisores persistentes.

## Transporte e redundância

O mesmo processo SYSTEM mantém:

1. **Vercel + Neon** — controle HTTP/MCP primário de baixa latência em `https://anthares-remote-primary.vercel.app`. O endpoint expõe OAuth, `/mcp`, heartbeat, leases, resultados idempotentes e estado persistente no Neon. Não depende de Cloudflare.
2. **GitLab private issue queue** — transporte independente de recuperação e administração, já comprovado em produção.
3. **GitHub private issue queue** — segunda rota independente de recuperação.

Cloudflare deixou de fazer parte do caminho canônico do Anthares Remote. O antigo endpoint Cloudflare pode permanecer apenas como histórico até remoção definitiva das integrações que ainda apontem para ele.

Não existe segundo agente para o HTTP. A redundância é de transporte dentro do mesmo processo, preservando single-writer e receipts idempotentes.

Render nunca é primário, obrigatório ou autoridade de estado.

## Regras de cutover

`windows/install-system-v8.ps1` é o único instalador canônico. Ele só conclui quando:

- scripts canônicos foram sincronizados e parseados;
- `.lastgood` existe para scripts críticos;
- o V4 possui baseline de hash;
- a credencial DPAPI LocalMachine das filas é carregável pelo SYSTEM;
- `anthares-remote-agent-v4-c8.exe` está em sessão 0;
- um job real `agent_health` atravessa uma fila privada;
- esse job confirma `queue_configured=true` e `http_control=true` no mesmo PID;
- somente depois disso tarefas/executores antigos são desativados.

`phase4-migrate-task.ps1` só aceita sucesso quando `queue_end_to_end_proof=true`, `mcp_http_transport_configured=true` e existe PID SYSTEM válido. Em falha, restaura o binário anterior.

## Recuperação local

O watchdog roda em SYSTEM e é independente dos serviços externos. Ele:

- garante as tarefas SYSTEM canônicas;
- impede executor Anthares em sessão interativa;
- valida a credencial privada sem imprimir segredos;
- restaura o V4 a partir de `anthares-remote-agent-v4.lastgood.exe` quando o hash diverge;
- restaura supervisor, loader e watchdog a partir de `.lastgood`;
- registra `queue_credential_present`, `queue_credential_loaded`, `system_v4_count` e `interactive_agent_count`.

Se o Vercel estiver indisponível, as filas privadas mantêm o processo operacional. Se uma fila estiver atrasada, o mesmo processo continua recebendo comandos MCP por Vercel.

## Interface gráfica autorizada (sessão do usuário)

O agente canônico continua **SYSTEM / sessão 0**, sem abrir janelas por shell.
Para abrir somente páginas HTTPS aprovadas em perfis Chrome já existentes, o
comando remoto autenticado aceita a forma estruturada:

`ara-desktop-open {"profile":"Profile 2","url":"https://chatgpt.com"}`

Essa ação **não executa PowerShell nem CMD**. O agente valida o perfil e o host,
obtém o token da sessão de console do Windows e solicita ao sistema a abertura
do executável Chrome instalado no desktop desse usuário. São permitidos apenas
os perfis Default, 2, 3, 5, 7, 8 e 9 e hosts aprovados de ChatGPT/Google.
Não há suporte a execução de código, foco arbitrário, cliques ou digitação livre
nessa operação. O shell ordinário permanece sob `headless_policy.go`.

A resposta `launched_not_authenticated` confirma somente a criação do processo. Não
confirma que a página terminou de carregar nem concede OAuth. Autorização de
contas Google e instalação/conexão de plugins continuam exigindo o fluxo de
consentimento do provedor e do ChatGPT. Nunca trate lançamento como conexão.

A funcionalidade é limitada à instalação Windows do dispositivo canônico,
onde o perfil Chrome está em `C:\Users\Lucas\AppData\Local\Google\Chrome\User Data`.
Em sessão de console inativa ou dispositivo diferente, falha de forma fechada.

## Diagnóstico

Prefira jobs tipados a shell. `agent_health` retorna PID, dispositivo, work root, `http_control`, `queue_configured`, providers de fila, diretório de receipts e contagem de receipts, sem segredos. `ping`, `system_info`, `safe_environment`, arquivos, processos, serviços e demais capacidades tipadas continuam disponíveis. Shell é escape hatch e deve permanecer oculto/não interativo.

## Caminhos legados aposentados

- Cloudflare Anthares Remote: fora do caminho canônico por esgotamento de cota;
- `.github/workflows/anthares-remote-agent-install-selfhosted.yml`: fail-closed;
- `infra/anthares_remote_bootstrap.py`: HTTP 410, sem mutações;
- `windows/watchdog-dual-supervisor.ps1`: não inicia supervisores;
- `windows/run-agent-user-fallback.ps1`: desativa executor de usuário;
- supervisores HTTP antigos: break-glass explícito apenas.

## Invariantes

- nenhuma porta de entrada no PC; somente conexões HTTPS de saída;
- nenhum segredo em repositório, logs ou resultados;
- credenciais privadas via DPAPI LocalMachine e ACL SYSTEM/Administrators;
- um executor por dispositivo;
- Vercel + Neon como controle primário;
- GitLab e GitHub como recuperação independente;
- writes ambíguos não são repetidos automaticamente;
- nenhuma janela visível de PowerShell/CMD;
- Cloudflare não é requisito operacional;
- CI falha se essas invariantes forem revertidas.
