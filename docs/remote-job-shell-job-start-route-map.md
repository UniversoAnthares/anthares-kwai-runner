# Mapa de rotas que criam jobs `shell` / `job_start` (inventário somente leitura)

Escopo: todo caminho, em qualquer repositório/branch deste workspace, capaz de criar
um job de tipo `shell` ou `job_start` (comando livre) no agente Windows.
Gerado por leitura de código, sem execução.

Legenda de **bloqueio**:
- **BLOQUEADO (MCP)** — o caminho passa pelo handler MCP do router de produção e é
  barrado por `BLOCKED_TOOLS` (HTTP 403 `tool_blocked`).
- **BLOQUEADO (v1/mcp/execute)** — barrado pelo mesmo conjunto no endpoint legado.
- **NÃO BLOQUEADO** — o caminho aceita `type: "shell"` / `"job_start"` e repassa ao agente.

---

## 1. Plano de controle de produção (Vercel / Neon) — `vercel-ara-primary/api/router.mjs`

| # | Caminho | Trecho | Cria shell/job_start? | Bloqueio |
|---|---|---|---|---|
| 1 | Tool MCP `remote_exec` | `router.mjs` — tool **removida** de `makeMcp`; `BLOCKED_TOOLS` contém `remote_exec` | antes: `execute('shell',{command,shell})` | **BLOQUEADO (MCP)** 403 `tool_blocked` |
| 2 | Tool MCP `remote_job_start` | `router.mjs` — `inputSchema:{command_id,args[],cwd?,timeout_seconds?}`; chama `executeRemoteJob(...)` que cria job de tipo **`remote_job`** | não cria mais `job_start`; só `remote_job` assinado | **BLOQUEADO (MCP)** para `job_start`; `remote_job_start` exige escopo `ara.exec` |
| 3 | Tool MCP `service_status` | `router.mjs` — `execute('shell',{command:'Get-Service -Name ...'})` | cria job `shell` **com comando fixo**, sem `command` do cliente | **NÃO BLOQUEADO** (comando fixo, `name` validado por regex `^[A-Za-z0-9_.-]{1,128}$`) — ver risco R1 |
| 4 | Endpoint legado `POST v1/mcp/execute` | `router.mjs` — `if(BLOCKED_TOOLS.has(type))return reply(res,403,{error:'tool_blocked',tool:type});` | aceitaria `type:"shell"` sem o check | **BLOQUEADO (v1/mcp/execute)** 403 `tool_blocked` (correção desta PR) |
| 5 | API do dispositivo `GET v1/device/jobs/next` | `router.mjs` — `leaseNext(a.device)` entrega o job mais antigo pronto | não cria; entrega | — |
| 6 | API do dispositivo `POST v1/device/jobs/:id/result` | `router.mjs` — `submitResult(a.device,m[1],jsonBody(req))` | não cria | — |

### Worker Cloudflare (cópia legada / gateway)
`cloudflare-ara-backup/src/index.js` linha 467 — `st.createJob(device, type, body.args || {}, timeout, idem)`:
aceita `type` arbitrário. **NÃO BLOQUEADO** neste arquivo (é a cópia legada do plano
de controle; a produção é Vercel). Risco R2.
`cloudflare-ara-mcp/src/index.js` linha 340 — `controlJson(env,"/v1/mcp/execute",{...type,args...})`:
encaminha para o `v1/mcp/execute` do backup; linha 409 mapeia `remote_exec -> ["shell",...]`
e `remote_job_start -> ["job_start",{command,...}]`. **NÃO BLOQUEADO** neste arquivo.
Risco R3 (é o gateway MCP com escopos `ara.read/ara.write`).

---

## 2. Bridges Python (infra) — ainda actifs no repositório

| # | Caminho | Trecho | Cria shell/job_start? | Bloqueio |
|---|---|---|---|---|
| 7 | `POST /v1/control/jobs` | `infra/anthares_remote_control_routes.py:158` — `job = enqueue_job(device, job_type, body.get("args") or {}, ...)` | **sim**, `job_type` livre do chamador | **NÃO BLOQUEADO** — R4 |
| 8 | `POST /v1/control/execute` | `infra/anthares_remote_control_routes.py:182` — `job = execute_job(device, job_type, body.get("args") or {}, timeout, ...)` | **sim**, `job_type` livre | **NÃO BLOQUEADO** — R4 |
| 9 | `POST /v1/bootstrap/diagnose` | `infra/anthares_remote_secure_bootstrap.py:48` — `job = _enqueue("shell", {"command": command, "shell": "powershell"}, 45)` | **sim**, `shell` com comando **fixo** (não vem do cliente) | **NÃO BLOQUEADO** — R5 (challenge-auth, comandos fixos) |
| 10 | `POST /v1/bootstrap/recover-runner` | `infra/anthares_remote_secure_bootstrap.py:64` — `job = _enqueue("shell", {"command": command, "shell": "powershell"}, 30)` | **sim**, `shell` com comando **fixo** | **NÃO BLOQUEADO** — R5 |
| 11 | `POST /v1/runtime/remote/execute` | `infra/anthares_runtime_mesh.py:212` — `finished = _remote_execute(device, job_type, body.get("args") or {}, timeout)` | **sim**, `job_type` livre | **NÃO BLOQUEADO** — R6 |
| 12 | `ara_canary_mcp_bridge.py` | `infra/ara_canary_mcp_bridge.py:97` — `job = _STORE.enqueue(device, job_type, args or {}, timeout, ...)` | **sim**, `job_type` livre | **NÃO BLOQUEADO** — R7 |
| 13 | Compat legada de estado | `infra/ara_legacy_state_compat.py:10` — `self.relay._store().enqueue(self.device, job.get("type") or "unknown", job.get("args") or {}, ...)` | **sim**, `type` vindo do job legado | **NÃO BLOQUEADO** — R7 |
| 14 | Store de estado | `infra/ara_state_store.py:56` e `:217` — `def enqueue(self, device_id, job_type, args=None, timeout_seconds=30, ...)` | camada de persistência | — |

---

## 3. Agente Go (Windows, SYSTEM) — `anthares-remote-agent/cmd/agent/main.go`

| # | Caminho | Trecho | Bloqueio |
|---|---|---|---|
| 15 | `case "shell"` | `main.go` — `if !cfg.AllowShell { return "", errors.New("shell disabled; set ANTHARES_ALLOW_SHELL=1 to enable") }` | depende de `ANTHARES_ALLOW_SHELL`; hoje está **1** (rodando) |
| 16 | `case "job_start"` | `main.go` — `if !cfg.AllowShell { ... "shell disabled" }` | idem |
| 17 | `case "remote_job"` | `main.go` — `return remoteJobJSON(ctx, cfg, job)` → exige assinatura ed25519 com escopo `ara.exec` | **BLOQUEADO** por assinatura (falta `ARA_CONTROL_PUBLIC_KEY_B64` até ser configurado) |

---

## Riscos abertos (não corrigidos nesta PR)

- **R1** `service_status` cria job `shell` com comando fixo. O cliente não controla o
  comando, mas o job é `shell` e depende de `ANTHARES_ALLOW_SHELL=1`.
- **R2** `cloudflare-ara-backup/src/index.js:467` aceita `type` arbitrário.
- **R3** `cloudflare-ara-mcp/src/index.js:409` ainda mapeia `remote_exec -> shell` e
  `remote_job_start -> job_start` (comando livre).
- **R4** `/v1/control/jobs` e `/v1/control/execute` aceitam `job_type` livre.
- **R5** `/v1/bootstrap/*` cria jobs `shell` com comandos fixos (challenge-auth).
- **R6** `/v1/runtime/remote/execute` aceita `job_type` livre.
- **R7** `ara_canary_mcp_bridge` e `ara_legacy_state_compat` enfileiram `job_type` livre.

Mitigação comum: desligar `ANTHARES_ALLOW_SHELL=1` no agente SYSTEM neutraliza R1..R7
no lado do agente, porque `shell` e `job_start` passam a exigir essa flag.
**Ação manual do dono** (não aplicada aqui, exige downtime do agente).
