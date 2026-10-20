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

## Política de interface: autorização, invisibilidade e silêncio

Regra obrigatória: o Anthares Remote não toma foco, não envia mouse/teclado
e não lê nem manipula a janela de trabalho do usuário sem uma aprovação
explícita **para aquela ação**. Enquanto não existir um mecanismo de aprovação
associado a escopo e validade, as operações `screenshot`, `clipboard_get`
e `clipboard_set` falham com `owner authorization required`.

A operação estruturada `ara-desktop-open` cria exclusivamente um **novo**
Chrome headless, com `--headless=new`, `--mute-audio`,
`--disable-audio-output`, inicialização de janela escondida e
`--no-first-run`. Utiliza um diretório de dados isolado em
`C:\Users\Lucas\AppData\Local\AntharesRemote\HeadlessChrome\<rotulo>`,
sem reutilizar o diretório de dados do Chrome aberto no desktop nem
reutilizar seus cookies, logins ou sessões.

Apenas os rótulos Default/Perfil 2/3/5/7/8/9 e URLs HTTPS de
ChatGPT/Google previamente permitidas podem ser escolhidos. O rótulo
identifica uma **sessão headless isolada**, não a conta Google do
perfil Chrome existente. Nenhuma autorização OAuth é concedida
pela abertura. O consentimento de instalação de plugins/contas
continua no fluxo oficial do ChatGPT e do Google, feito pelo titular.

O `process_start` genérico recusa binários GUI e aceita apenas um
pequeno conjunto de executáveis CLI previamente allowlistados;
`process_kill` recusa processos da sessão interativa do usuário.
O filtro de shell `headless_policy.go` continua obrigatório.

O agente principal ainda opera como SYSTEM na sessão 0, preservando
watchdog e transportes de recuperação. A criação headless usa apenas o
token da sessão ativa, sem acionar, ativar ou selecionar janelas do usuário.
Para qualquer operação que realmente exija interagir com uma janela
existente, o sistema deve parar e solicitar autorização específica.

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
