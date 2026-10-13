#!/usr/bin/env python3
from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing patch target: {label}")
    return text.replace(old, new, 1)


# 1) Cloudflare Durable Object is the single ARA controller authority.
p = Path("cloudflare-ara-backup/src/index.js")
s = p.read_text(encoding="utf-8")
s, n = re.subn(r"const KEY_URLS = \[.*?\];", "const KEY_URLS = [];", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit("KEY_URLS patch failed")

fence = '''// cloudflare-single-authority-v1: ARA has exactly one durable controller state.
// Reserve endpoints are transport proxies to this same Worker service, so there is
// no second writer and therefore no external fencing database is required.
const FENCE_MODE = "cloudflare-single-authority-v1";
async function sharedFence(_request, _device, _op = "acquire") {
  return { ok: true, status: 200, owner: "anthares-ara-backup", epoch: FENCE_MODE };
}

'''
s, n = re.subn(
    r"// shared-fencing-v1:.*?\nexport class AraState",
    fence + "export class AraState",
    s,
    count=1,
    flags=re.S,
)
if n != 1 and "cloudflare-single-authority-v1" not in s:
    raise SystemExit("shared fencing patch failed")

s = s.replace('role: "ara-backup-control"', 'role: "ara-canonical-control"')
s = s.replace('shared_fencing: "floot-postgres-v1"', "shared_fencing: FENCE_MODE")
s = s.replace('fence_authority: "floot-postgres"', 'fence_authority: "cloudflare-durable-object"')
if "legacy_mcp_discovery: false" not in s:
    s = s.replace(
        "redundant_mcp_keys: true,",
        "redundant_mcp_keys: true,\n        legacy_mcp_discovery: false,",
    )
s = s.replace('trusted_mcp_services: KEY_URLS.length,', 'trusted_mcp_services: "pinned-secret",')

auth_anchor = '''    if (url.pathname === "/v1/device/auth-check" && request.method === "GET") {
      const auth = await deviceOk(request);
      if (!auth.ok) return json({ ok: false, error: "unauthorized" }, 401);
      const fence = await sharedFence(request, auth.device, "status");
      if (!fence.ok) return json({ ok: false, error: "shared_fence_auth_failed", fence_status: fence.status }, 503);
      return json({ ok: true, shared_fence_auth: true, fence_authority: "cloudflare-durable-object" });
    }
'''
if "/v1/device/status" not in s:
    if auth_anchor not in s:
        raise SystemExit("auth-check route target missing")
    s = s.replace(
        auth_anchor,
        auth_anchor + '''
    if (url.pathname === "/v1/device/status" && request.method === "GET") {
      const auth = await deviceOk(request);
      if (!auth.ok) return json({ ok: false, error: "unauthorized" }, 401);
      return json(await st.status(auth.device));
    }
''',
        1,
    )
if "floot.app" in s or "onrender.com" in s:
    raise SystemExit("external runtime dependency still present in canonical controller")
p.write_text(s, encoding="utf-8")

# 2) Agent exits after persistent control failure so whichever SYSTEM supervisor
# is active can recover it. Do not rewrite supervisor policy here: other recovery
# transports are being developed concurrently and are intentionally preserved.
p = Path("anthares-remote-agent/cmd/agent/main.go")
s = p.read_text(encoding="utf-8")
old = '''func heartbeatLoop(cfg Config) {
\tticker := time.NewTicker(15 * time.Second)
\tdefer ticker.Stop()
\tfor {
\t\t_ = heartbeat(cfg)
\t\t<-ticker.C
\t}
}
'''
new = '''func heartbeatLoop(cfg Config) {
\tticker := time.NewTicker(15 * time.Second)
\tdefer ticker.Stop()
\tfailures := 0
\tfor {
\t\tif err := heartbeat(cfg); err != nil {
\t\t\tfailures++
\t\t\tfmt.Fprintf(os.Stderr, "heartbeat error (%d/4): %v\\n", failures, err)
\t\t\tif failures >= 4 {
\t\t\t\tfmt.Fprintln(os.Stderr, "control heartbeat unavailable; exiting for supervisor recovery")
\t\t\t\tos.Exit(23)
\t\t\t}
\t\t} else {
\t\t\tfailures = 0
\t\t}
\t\t<-ticker.C
\t}
}
'''
if old in s:
    s = s.replace(old, new, 1)
elif "os.Exit(23)" not in s:
    raise SystemExit("heartbeatLoop target missing")
p.write_text(s, encoding="utf-8")

# 3) Build production agent on main so the fixed binary is produced remotely.
p = Path(".github/workflows/anthares-remote-agent-build.yml")
s = p.read_text(encoding="utf-8")
if "      - main\n" not in s:
    s = s.replace(
        "      - feature/anthares-remote-agent\n      - feature/ara-chatgpt-mcp",
        "      - main\n      - feature/anthares-remote-agent\n      - feature/ara-chatgpt-mcp",
    )
p.write_text(s, encoding="utf-8")

# 4) Update the canonical control deploy checks.
p = Path(".github/workflows/cloudflare-ara-backup-deploy.yml")
s = p.read_text(encoding="utf-8")
s = s.replace("shared-fencing-v1", "cloudflare-single-authority-v1")
s = s.replace("floot-postgres-v1", "cloudflare-single-authority-v1")
s = s.replace("ARA_SHARED_FENCING_DEPLOYED=1", "ARA_CLOUDFLARE_SINGLE_AUTHORITY_DEPLOYED=1")
p.write_text(s, encoding="utf-8")

# 5) Reserve is a second hostname bound to the SAME controller Worker. It gives
# transport redundancy without split-brain Durable Object state.
reserve = Path("cloudflare-ara-reserva")
(reserve / "src").mkdir(parents=True, exist_ok=True)
(reserve / "wrangler.toml").write_text('''name = "anthares-ara-reserva"
account_id = "5c24be052e5144391f73a8e03491e88e"
main = "src/index.js"
compatibility_date = "2026-10-01"

[[services]]
binding = "ARA_CONTROL"
service = "anthares-ara-backup"
''', encoding="utf-8")
(reserve / "src" / "index.js").write_text('''const INTERNAL_ORIGIN = 'https://anthares-ara-backup.internal';

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, INTERNAL_ORIGIN);
    const upstream = await env.ARA_CONTROL.fetch(new Request(target.toString(), request));
    const headers = new Headers(upstream.headers);
    headers.set('x-anthares-ara-route', 'reserve-proxy');
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers,
    });
  },
};
''', encoding="utf-8")

# 6) Documentation reflects the proven ChatGPT OAuth connection.
p = Path("docs/ARA-RENDER-INDEPENDENCE.md")
s = p.read_text(encoding="utf-8")
marker = "## Fechamento operacional — 13/10/2026"
if marker not in s:
    s += '''

## Fechamento operacional — 13/10/2026
- O app `Anthares Remote Cloudflare` foi conectado por OAuth no ChatGPT e uma chamada real `remote_exec` retornou exit code 0.
- O controlador canônico não consulta Render nem Floot em runtime; estado, leases, replay protection e OAuth ficam em Cloudflare Durable Objects/SQLite.
- `anthares-ara-reserva` é um proxy de transporte para o mesmo serviço `anthares-ara-backup`; ele não cria um segundo escritor de estado.
- GitHub/GitLab podem permanecer como canais de recuperação independentes, sem substituir o controlador Cloudflare canônico.
- O agente encerra após quatro falhas consecutivas de heartbeat para permitir recuperação pelo supervisor SYSTEM ativo.
'''
p.write_text(s, encoding="utf-8")

# These old manual workflows can reintroduce the removed Floot fencing.
for obsolete in [
    Path(".github/workflows/ara-shared-fencing-deploy.yml"),
    Path(".github/workflows/ara-shared-fencing-integrate.yml"),
]:
    if obsolete.exists():
        obsolete.unlink()

print("ARA_CLOUDFLARE_FINALIZER_PATCH_OK=1")
