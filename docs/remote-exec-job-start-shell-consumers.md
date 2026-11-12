# Inventário somente leitura: quem chama `remote_exec`, `job_start` e `shell`

Escopo: leitura de código em todos os repositórios/branch deste workspace
(`anthares-kwai-runner` @ main e branch `claude/ara-remote-job-security`).
Nenhuma alteração feita nos itens listados; apenas registro do consumidor,
do caminho e do comando típico.

Legenda de impacto:
- **ALTO** — permite execução de comando arbitrário no Windows.
- **MEDIO** — o comando é fixo no código (não controlável pelo cliente), mas o job
  criado é do tipo `shell`.
- **BAIXO** — apenas lista/espera o nome da ferramenta, ou é QA que já espera 403.

---

## 1. Workflows do GitHub (`.github/workflows/`)

| Consumidor | Caminho | Comando típico | Impacto |
|---|---|---|---|
| `anthares-ssh-monitor.yml` | `.github/workflows/anthares-ssh-monitor.yml:44-46` | `python scripts/ssh-admission.py monitor --device ...` (aciona SSH por SSH, não via `shell` do MCP) | BAIXO |
| `anthares-ssh-recovery.yml` | `.github/workflows/anthares-ssh-recovery.yml:69-79` | `python scripts/ssh-admission.py recover --device ...` | BAIXO |
| `item6-android-remote-proof.yml` | `.github/workflows/item6-android-remote-proof.yml:12` | job `android_remote_executor` (não usa `remote_exec`/`shell` do MCP) | BAIXO |

**Nenhum workflow no repositório chama a ferramenta MCP `remote_exec`, `job_start` ou o
tipo de job `shell`.** A recuperação SSH usa SSH direto (`ssh-keyscan`/`ssh`), não o
agente MCP.

## 2. Scripts Python (`scripts/`, `infra/`)

| Consumidor | Caminho | Comando típico | Impacto |
|---|---|---|---|
| `ssh-admission.py` | `scripts/ssh-admission.py` (invocado pelos 2 workflows acima) | `recover`/`probe` por SSH | BAIXO |
| `anthares_remote_secure_bootstrap.py` | `infra/anthares_remote_secure_bootstrap.py:48` | `_enqueue("shell", {"command": <PowerShell fixo de diagnóstico>})` | MEDIO |
| `anthares_remote_secure_bootstrap.py` | `infra/anthares_remote_secure_bootstrap.py:64` | `_enqueue("shell", {"command": <PowerShell fixo de recuperação do runner>})` | MEDIO |
| `anthares_remote_control_routes.py` | `infra/anthares_remote_control_routes.py:158` | `enqueue_job(device, job_type, body["args"], ...)` — `job_type` livre | ALTO |
| `anthares_remote_control_routes.py` | `infra/anthares_remote_control_routes.py:182` | `execute_job(device, job_type, body["args"], ...)` — `job_type` livre | ALTO |
| `anthares_runtime_mesh.py` | `infra/anthares_runtime_mesh.py:212` | `_remote_execute(device, job_type, body["args"], ...)` — `job_type` livre | ALTO |
| `ara_canary_mcp_bridge.py` | `infra/ara_canary_mcp_bridge.py:97` | `_STORE.enqueue(device, job_type, args, ...)` — `job_type` livre | ALTO |
| `ara_legacy_state_compat.py` | `infra/ara_legacy_state_compat.py:10` | `enqueue(self.device, job.get("type") or "unknown", ...)` | ALTO |
| `anthares_remote_control_routes.py` (capabilities) | `infra/anthares_remote_control_routes.py:209-211` | lista `"shell"`, `"job_start"` entre as capabilities | BAIXO |
| `ara_canary_mcp_bridge.py` (capabilities) | `infra/ara_canary_mcp_bridge.py:180-184` | lista `"shell"`, `"job_start"` | BAIXO |

## 3. MCP / control plane (JavaScript)

| Consumidor | Caminho | Comando típico | Impacto |
|---|---|---|---|
| `remote-server.mjs` (cópia legada) | `anthares-remote-mcp/remote-server.mjs:40` | `execute('shell',{command,shell})` via tool `remote_exec` | ALTO |
| `remote-server.mjs` (cópia legada) | `anthares-remote-mcp/remote-server.mjs:51` | `execute('job_start',{command,name})` via tool `remote_job_start` | ALTO |
| `server.mjs` (cópia legada) | `anthares-remote-mcp/server.mjs:81` | tool `remote_exec` | ALTO |
| `server.mjs` (cópia legada) | `anthares-remote-mcp/server.mjs:203-206` | tool `remote_job_start` → `execute('job_start',{command,name})` | ALTO |
| `gateway.mjs` (cópia legada) | `anthares-remote-mcp/gateway.mjs:14` | `WRITE_TOOLS` inclui `remote_exec`, `remote_job_start` | MEDIO |
| `gateway-v2.mjs` (cópia legada) | `anthares-remote-mcp/gateway-v2.mjs:12` | `WRITE_TOOLS` inclui `remote_exec`, `remote_job_start` | MEDIO |
| `cloudflare-ara-mcp/src/index.js` (gateway Cloudflare) | `cloudflare-ara-mcp/src/index.js:15` | `WRITE_TOOLS` inclui `remote_exec`, `remote_job_start` | MEDIO |
| `cloudflare-ara-mcp/src/index.js` | `cloudflare-ara-mcp/src/index.js:346` | tool `remote_exec` (`command` livre) | ALTO |
| `cloudflare-ara-mcp/src/index.js` | `cloudflare-ara-mcp/src/index.js:368` | tool `remote_job_start` (`command` livre) | ALTO |
| `cloudflare-ara-mcp/src/index.js` | `cloudflare-ara-mcp/src/index.js:409` | mapa `remote_exec -> ["shell",{command}]`, `remote_job_start -> ["job_start",{command}]` | ALTO |
| `cloudflare-ara-mcp/src/index.js` | `cloudflare-ara-mcp/src/index.js:412` | `timeout = name === "remote_exec" ? a.timeout_seconds \|\| 30 : ...` | BAIXO |
| `cloudflare-ara-backup/src/index.js` | `cloudflare-ara-backup/src/index.js:18-22` | capabilities listam `"shell"` e `"job_start"` | BAIXO |
| `vercel-ara-primary/api/router.mjs` (**produção**) | `vercel-ara-primary/api/router.mjs:18` | `BLOCKED_TOOLS` bloqueia `shell`, `job_start`, `remote_exec` | — (corrigido) |

## 4. QA / testes que citam as ferramentas

| Consumidor | Caminho | Comando típico | Impacto |
|---|---|---|---|
| `remote-qa.mjs` | `anthares-remote-mcp/remote-qa.mjs:11` | exige `remote_exec` e `remote_job_start` na lista de tools | BAIXO (quebra se forem removidas) |
| `qa.mjs` | `anthares-remote-mcp/qa.mjs:65,69` | idem | BAIXO |
| `oauth-qa.mjs` | `anthares-remote-mcp/oauth-qa.mjs:45` | chama `remote_exec` e **espera 403** para token read-only | BAIXO |
| `owner-github-auth.test.mjs` | `cloudflare-ara-mcp/src/owner-github-auth.test.mjs:71` | afirma que `remote_exec` **não** aparece para o dono GitHub | BAIXO |
| `owner-github-auth.test.mjs` | `cloudflare-ara-mcp/src/owner-github-auth.test.mjs:98` | afirma que `remote_exec` **aparece** no token com escopo de escrita | MÉDIO — conflita com o bloqueio novo |

## 5. CORTES / publicações

| Consumidor | Caminho | Comando típico | Impacto |
|---|---|---|---|
| `android_executor_router.py` | `tools/android_executor_router.py:115` | `return "secondary_remote_executor"` — apenas rótulo de executor | BAIXO |
| `gitlab-runner-render/custom_executor.py` | `infra/gitlab-runner-render/custom_executor.py:291-293` | `shell = "/bin/bash"`/`"/bin/sh"` — shell de **container Linux** do runner, não do Windows | BAIXO |
| `gitlab-runner-render/runner_service.py` | `infra/gitlab-runner-render/runner_service.py:51` | `"--shell"` — flag do runner | BAIXO |
| `ara_canary_app.py` | `infra/ara_canary_app.py:100` | `_durable_store.enqueue(...)` — enfileira job do canário (tipo vindo do caller) | MÉDIO |

**Nenhum consumidor CORTES/publicação chama a tool MCP `remote_exec` ou cria job
`job_start`/`shell` diretamente.** As publicações usam o executor de container Linux.

---

## Conclusão

1. **Nenhum workflow do GitHub** executa `remote_exec`/`job_start`/`shell` pelo MCP.
2. **Os consumidores de alto risco** são: as 4 bridges Python com `job_type` livre
   (`/v1/control/jobs`, `/v1/control/execute`, `/v1/runtime/remote/execute`,
   `ara_canary_mcp_bridge`/`ara_legacy_state_compat`) e as cópias legadas do MCP
   (`anthares-remote-mcp/*`, `cloudflare-ara-mcp/src/index.js`).
3. **O caminho de produção (Vercel) está bloqueado** nesta PR.
4. **Falta desativar as cópias legadas** (`anthares-remote-mcp/server.mjs`,
   `remote-server.mjs`, `gateway*.mjs`, `cloudflare-ara-mcp/src/index.js`) ou
   confirmar que não estão deployadas — não foi possível confirmar o estado de
   deploy sem credenciais de serviço.
5. **`owner-github-auth.test.mjs:98`** passa a falhar se o bloqueio for replicado no
   `cloudflare-ara-mcp` — precisa ser atualizado junto.
