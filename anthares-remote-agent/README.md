# Anthares Remote Agent

Anthares Remote é o canal canônico de administração remota do Windows do projeto Anthares. O runtime não depende de AI Commander, Desktop Commander ou Render como requisito operacional.

## Runtime canônico no Windows

O dispositivo autorizado é `DESKTOP-FTDK0HP`.

A execução persistente usa a tarefa agendada `Anthares Remote Agent SYSTEM`, em `SYSTEM`, `Highest`, sessão 0 e PowerShell não interativo/oculto.

O supervisor canônico é `windows/run-agent-system-supervisor.ps1`. Ele usa as filas privadas GitHub/GitLab e mantém uma única instância do agente para evitar leases e resultados duplicados. Não há controlador HTTP obrigatório nesse caminho.

## Plano de controle redundante

Caminho canônico:

1. fila privada GitHub/GitLab — transporte V4 do agente;
2. Cloudflare `https://anthares-ara-backup.anthares1.workers.dev` — controlador HTTP durável independente;
3. Northflank `https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run` — redundância de compute/control;
4. Render — somente fallback final de emergência enquanto a cota gratuita ainda existir.

Os supervisores HTTP legados devem seguir essa mesma ordem: Cloudflare -> Northflank -> Render. Nenhuma URL `onrender.com` pode ser primária ou única.

## Estado e MCP

- controle durável principal: Cloudflare Durable Objects/SQLite;
- banco externo redundante: Neon (`anthares-ara-ha`);
- MCP/OAuth canônico: `https://anthares-ara-mcp.anthares1.workers.dev/mcp`;
- compute/container que exige Chromium: Northflank;
- Render não é autoridade de estado nem requisito de autenticação.

## Segurança

- Nenhuma porta de entrada precisa ser aberta no PC.
- O agente inicia somente conexões HTTPS de saída.
- O runtime canônico roda em sessão 0 e não deve abrir ou manipular a área de trabalho interativa.
- O token do dispositivo permanece somente no host; o repositório publica apenas seu SHA-256 por identidade autorizada.
- Tokens e outros segredos nunca devem ser commitados.
- Acesso a arquivos e processos continua sujeito às allowlists do agente.
- Shell remoto exige `ANTHARES_ALLOW_SHELL=1`.
- Jobs têm timeout e ciclo de lease/resultado persistente.

## Arquivos principais

- `cmd/agent`: agente Windows em Go.
- `windows/run-agent-system-supervisor.ps1`: supervisor SYSTEM canônico por filas privadas.
- `windows/run-agent-supervisor.ps1`: compatibilidade HTTP; Cloudflare/Northflank antes de Render.
- `windows/run-agent-standard.ps1`: compatibilidade da identidade padrão; mesma ordem de fallback.
- `windows/watchdog-dual-supervisor.ps1`: recuperação legada com standby Northflank.
- `cloudflare-ara-backup/`: controlador durável Cloudflare.
- `cloudflare-ara-mcp/`: MCP/OAuth canônico.

## Regra operacional

Novas funções de administração remota devem ser implementadas no Anthares Remote sem introduzir dependência obrigatória de Render. Render permanece somente como último fallback até sua retirada definitiva.
