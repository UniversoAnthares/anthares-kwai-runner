# Anthares Remote Agent

MVP de agente remoto próprio para máquinas Windows do projeto Anthares.

## Objetivo

Substituir gradualmente a dependência de serviços de acesso remoto de terceiros por um agente controlado pelo próprio projeto, com conexão de saída HTTPS, autenticação explícita e superfície de comandos limitada.

## Componentes

- `cmd/agent`: agente Windows em Go.
- `worker`: control plane Cloudflare Worker + Durable Object.
- `.github/workflows/anthares-remote-agent-build.yml`: compila o `.exe` Windows.

## Operações atuais

O agente aceita somente tipos de job conhecidos:

- `ping`
- `system_info`
- `process_list`
- `clipboard_get`
- `clipboard_set`
- `file_read`
- `file_write`
- `shell` (desligado por padrão; exige `ANTHARES_ALLOW_SHELL=1`)

Acesso a arquivos também fica desligado até que `ANTHARES_ALLOWED_ROOTS` seja configurado. O limite por arquivo/resultado é 1 MiB no MVP.

## Variáveis do agente

```text
ANTHARES_CONTROL_URL=https://SEU-WORKER.workers.dev
ANTHARES_DEVICE_TOKEN=<segredo-do-dispositivo>
ANTHARES_DEVICE_ID=DESKTOP-FTDK0HP
ANTHARES_ALLOWED_ROOTS=C:\Users\Lucas;C:\ProgramData\AntharesRemoteAgent
ANTHARES_ALLOW_SHELL=0
```

Nunca faça commit dos tokens.

## Worker

No diretório `worker`:

```bash
npx wrangler secret put DEVICE_TOKEN
npx wrangler secret put CONTROL_TOKEN
npx wrangler deploy
```

`DEVICE_TOKEN` autentica exclusivamente o agente. `CONTROL_TOKEN` autentica quem cria e consulta jobs.

## API de controle

Criar job:

```http
POST /v1/control/jobs
Authorization: Bearer <CONTROL_TOKEN>
Content-Type: application/json

{
  "device_id": "DESKTOP-FTDK0HP",
  "type": "ping",
  "args": {},
  "timeout_seconds": 30
}
```

Consultar job:

```http
GET /v1/control/jobs/<JOB_ID>?device_id=DESKTOP-FTDK0HP
Authorization: Bearer <CONTROL_TOKEN>
```

Status do dispositivo:

```http
GET /v1/control/status?device_id=DESKTOP-FTDK0HP
Authorization: Bearer <CONTROL_TOKEN>
```

## Segurança do MVP

- Nenhuma porta de entrada precisa ser aberta no PC.
- O agente inicia conexões HTTPS para o Worker.
- Token do dispositivo e token de controle são separados.
- Shell é opt-in.
- Arquivos só podem ser acessados dentro de raízes explicitamente permitidas.
- Jobs têm timeout máximo de 120 segundos.
- O Worker mantém fila e resultados por dispositivo em Durable Object.

## Próxima etapa

1. Comprovar build Windows no GitHub Actions.
2. Implantar o Worker em `anthares1.workers.dev` ou domínio dedicado.
3. Gerar tokens aleatórios fora do repositório.
4. Instalar o `.exe` em uma máquina de teste e comprovar `ping`, heartbeat e clipboard.
5. Criar um MCP `AntharesRemote_MCP` sobre a API de controle.
6. Trocar tokens estáticos por identidade Ed25519 por dispositivo e adicionar rotação/revogação.
7. Adicionar serviço Windows, atualização assinada, screenshot e jobs assíncronos longos.
