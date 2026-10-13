# Anthares Remote Agent

Anthares Remote é o canal canônico de administração remota do Windows do projeto Anthares. O runtime não depende de AI Commander, Desktop Commander ou outro agente remoto como fallback.

## Runtime canônico no Windows

O dispositivo autorizado é `DESKTOP-FTDK0HP`.

A execução persistente usa a tarefa agendada `Anthares Remote Agent SYSTEM`, em `SYSTEM`, `Highest`, sessão 0 e PowerShell não interativo/oculto. A tarefa possui gatilho de boot e verificação periódica de 1 minuto; `MultipleInstances=IgnoreNew` impede supervisores duplicados.

O supervisor canônico é:

```text
C:\ProgramData\AntharesRemoteAgent\run-agent-system-supervisor.ps1
```

A fonte versionada correspondente é `windows/run-agent-system-supervisor.ps1`.

O supervisor mantém uma única instância do agente para evitar leases e resultados duplicados.

## Plano de controle redundante

Ordem normal:

1. `https://anthares-ara-control.onrender.com` — primário, estado durável PostgreSQL.
2. `https://anthares-ara-infra-canary-v2.onrender.com` — redundância Render/PostgreSQL.
3. `https://anthares-ara-backup.anthares1.workers.dev` — redundância independente em Cloudflare Durable Object/SQLite.

O supervisor troca de controlador após falhas consecutivas e retorna ao primário somente depois de uma sequência estável de health checks. Os arquivos `force-secondary.flag` e `force-tertiary.flag` existem apenas para testes controlados de failover.

O watchdog/keep-warm mantém o segundo serviço Render aquecido para evitar que cold start elimine a utilidade do failover rápido.

## Segurança

- Nenhuma porta de entrada precisa ser aberta no PC.
- O agente inicia somente conexões HTTPS de saída.
- O runtime canônico roda em sessão 0 e não deve abrir ou manipular a área de trabalho interativa.
- O token do dispositivo permanece somente no host; o repositório publica apenas seu SHA-256 por identidade autorizada.
- Tokens e outros segredos nunca devem ser commitados.
- O MCP usa autenticação de serviço assinada; o dispositivo usa seu token próprio.
- Acesso a arquivos e processos continua sujeito às allowlists do agente.
- Shell remoto exige `ANTHARES_ALLOW_SHELL=1`.
- Jobs têm timeout e ciclo de lease/resultado persistente.

## Arquivos principais

- `cmd/agent`: agente Windows em Go.
- `windows/run-agent-system-supervisor.ps1`: supervisor SYSTEM canônico.
- `windows/run-agent-supervisor.ps1`: supervisor de compatibilidade/fallback de instalação.
- `windows/run-agent-standard.ps1`: supervisor de compatibilidade da identidade padrão.
- `windows/watchdog-dual-supervisor.ps1`: keep-warm e recuperação de instalações legadas.
- `devices/*.sha256`: hashes públicos dos tokens dos dispositivos autorizados.
- `cloudflare-ara-backup/`: controlador independente Cloudflare.

## Contrato do agente

O agente expõe somente operações conhecidas pelo protocolo Anthares Remote, incluindo status, informações do sistema, processos, serviços, arquivos, shell controlado e jobs destacados. O conjunto efetivo é informado pelo endpoint de capabilities do plano de controle.

## Regra operacional

Novas funções de administração remota do PC devem ser implementadas no Anthares Remote. Não reintroduzir agentes remotos de terceiros como dependência ou redundância do canal canônico.
