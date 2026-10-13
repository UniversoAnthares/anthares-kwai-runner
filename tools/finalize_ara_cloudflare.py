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

# 2) Preserve concurrent V4 issue-queue work, while making Cloudflare HTTP
# control self-contained and recoverable. Queue transports remain additional
# recovery channels; they are not replaced or disabled here.
p = Path("anthares-remote-agent/windows/run-agent-system-supervisor.ps1")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "# Canonical runtime: one SYSTEM agent, one device identity, no interactive desktop.\n# GitHub and GitLab issue queues are independent transports and automatically\n# back each other up. Render and Cloudflare are intentionally not referenced.",
    "# Canonical runtime: one SYSTEM agent, one device identity, no interactive desktop.\n# Cloudflare is the primary signed HTTP control. GitHub/GitLab issue queues remain\n# independent recovery transports. Render is intentionally not referenced.",
)

http_pattern = r"\$httpCandidates = @\(.*?\) \| Where-Object \{ -not \[string\]::IsNullOrWhiteSpace\(\$_\) \} \| Select-Object -Unique"
http_repl = '''$primaryControl = if ([string]::IsNullOrWhiteSpace($env:ANTHARES_CONTROL_PRIMARY_URL)) { 'https://anthares-ara-backup.anthares1.workers.dev' } else { ([string]$env:ANTHARES_CONTROL_PRIMARY_URL).TrimEnd('/') }
$secondaryControl = if ([string]::IsNullOrWhiteSpace($env:ANTHARES_CONTROL_SECONDARY_URL)) { 'https://anthares-ara-reserva.anthares1.workers.dev' } else { ([string]$env:ANTHARES_CONTROL_SECONDARY_URL).TrimEnd('/') }
$httpCandidates = @(
    $primaryControl,
    $secondaryControl,
    ([string]$env:ANTHARES_CONTROL_TERTIARY_URL).TrimEnd('/')
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique'''
s, n = re.subn(http_pattern, lambda _: http_repl, s, count=1, flags=re.S)
if n != 1 and "anthares-ara-reserva.anthares1.workers.dev" not in s:
    raise SystemExit("http candidate patch failed")

control_pattern = r"function Test-Control\(\[string\]\$origin\) \{.*?\n\}"
control_repl = '''function Invoke-DeviceGet([string]$origin, [string]$path) {
    if ([string]::IsNullOrWhiteSpace($origin)) { return $null }
    if ($origin -notmatch '^https://') { return $null }
    try {
        $headers = @{
            Authorization = ('Bearer ' + $env:ANTHARES_DEVICE_TOKEN)
            'X-Anthares-Device' = $env:ANTHARES_DEVICE_ID
        }
        return Invoke-RestMethod -Method Get -Uri ($origin + $path) -Headers $headers -TimeoutSec 12
    } catch { return $null }
}

function Test-Control([string]$origin) {
    $r = Invoke-DeviceGet $origin '/v1/device/auth-check'
    return ($null -ne $r -and $r.ok -eq $true)
}

function Test-AgentConnected {
    foreach ($candidate in $httpCandidates) {
        $r = Invoke-DeviceGet $candidate '/v1/device/status'
        if ($null -ne $r -and $r.connected -eq $true) { return $true }
    }
    return $false
}'''
s, n = re.subn(control_pattern, lambda _: control_repl, s, count=1, flags=re.S)
if n != 1 and "function Test-AgentConnected" not in s:
    raise SystemExit("supervisor control probe patch failed")

if "$existingStaleSince = $null" not in s:
    mutex_line = "$mutex = New-Object System.Threading.Mutex($true, 'Global\\AntharesRemoteSystemSupervisorV4', [ref]$created)\nif (-not $created) { exit 0 }"
    s = replace_once(
        s,
        mutex_line,
        mutex_line + "\n$existingStaleSince = $null",
        "supervisor stale timer",
    )

existing_pattern = r"        # Never terminate an agent this supervisor did not start\..*?        if \(\$existing.Count -gt 0\) \{.*?            continue\n        \}\n"
existing_repl = '''        # Preserve a healthy agent started by another recovery channel. A live
        # process without a current authenticated Cloudflare heartbeat is not healthy:
        # after a grace period V4 replaces it so stale processes cannot block recovery.
        $existing = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) {
            if (Test-AgentConnected) {
                Save-State '' 'preserve-existing' 'existing-agent-healthy' $existing[0].Id
                $existingStaleSince = $null
                Start-Sleep -Seconds 10
                continue
            }
            if ($null -eq $existingStaleSince) { $existingStaleSince = Get-Date }
            if (((Get-Date) - $existingStaleSince).TotalSeconds -lt 45) {
                Save-State '' 'preserve-existing' 'existing-agent-heartbeat-stale-grace' $existing[0].Id
                Start-Sleep -Seconds 5
                continue
            }
            Save-State '' 'recovery' 'replacing-stale-existing-agent' $existing[0].Id
            foreach ($ep in $existing) { try { Stop-Process -Id $ep.Id -Force -ErrorAction SilentlyContinue } catch {} }
            $existingStaleSince = $null
            Start-Sleep -Seconds 2
            continue
        }
        $existingStaleSince = $null
'''
s, n = re.subn(existing_pattern, lambda _: existing_repl, s, count=1, flags=re.S)
if n != 1 and "replacing-stale-existing-agent" not in s:
    raise SystemExit("existing-agent recovery patch failed")
p.write_text(s, encoding="utf-8")

# 3) A persistently broken HTTP heartbeat must not leave a zombie process that
# prevents supervisor recovery. Four consecutive failures = controlled exit.
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

# 4) Build production agent on main.
p = Path(".github/workflows/anthares-remote-agent-build.yml")
s = p.read_text(encoding="utf-8")
if "      - main\n" not in s:
    s = s.replace(
        "      - feature/anthares-remote-agent\n      - feature/ara-chatgpt-mcp",
        "      - main\n      - feature/anthares-remote-agent\n      - feature/ara-chatgpt-mcp",
    )
p.write_text(s, encoding="utf-8")

# 5) Update the canonical control deploy checks.
p = Path(".github/workflows/cloudflare-ara-backup-deploy.yml")
s = p.read_text(encoding="utf-8")
s = s.replace("shared-fencing-v1", "cloudflare-single-authority-v1")
s = s.replace("floot-postgres-v1", "cloudflare-single-authority-v1")
s = s.replace("ARA_SHARED_FENCING_DEPLOYED=1", "ARA_CLOUDFLARE_SINGLE_AUTHORITY_DEPLOYED=1")
p.write_text(s, encoding="utf-8")

# 6) Reserve is a second transport hostname bound to the SAME controller Worker.
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

# 7) Documentation reflects the proven ChatGPT OAuth connection.
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
- O agente encerra após falha persistente de heartbeat e o supervisor V4 substitui processos vivos porém sem heartbeat atual, sempre em SYSTEM/sessão 0 e sem janelas interativas.
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
