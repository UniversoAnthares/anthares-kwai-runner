"""Ephemeral, challenge-authenticated bootstrap actions for Anthares Remote."""
import base64
import os
import secrets
import time
from flask import jsonify, request
import anthares_remote_control_routes as _relay

_DEVICE = "DESKTOP-FTDK0HP"
_ALLOWED = {}


def _authorized():
    if os.getenv("ARA_BOOTSTRAP_ACTIVE", "") == "1": return True
    supplied = request.headers.get("X-Anthares-Bootstrap", "")
    expected = os.getenv("ARA_BROWSER_APPROVED_CHALLENGE", "")
    return bool(supplied and expected) and secrets.compare_digest(supplied, expected)


def _enqueue(job_type, args=None, timeout=60):
    job_id = secrets.token_hex(16)
    job = {"id":job_id,"type":job_type,"args":args or {},"timeout_seconds":max(1,min(int(timeout),120)),"created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"status":"queued"}
    with _relay._LOCK:
        state = _relay._DEVICES.setdefault(_DEVICE,{"heartbeat":None,"queue":[],"jobs":{}})
        state["jobs"][job_id]=job; state["queue"].append(job_id)
    _ALLOWED[job_id]=time.time()+900
    return job


def register(app):
    @app.post("/v1/bootstrap/diagnose")
    def diagnose():
        if not _authorized(): return jsonify(error="unauthorized"),401
        command=r"""
$ErrorActionPreference='Continue'
'WHO='+(whoami)
$node=Get-Command node -ErrorAction SilentlyContinue; 'NODE='+[bool]$node; if($node){node --version}
$npm=Get-Command npm -ErrorAction SilentlyContinue; 'NPM='+[bool]$npm
$tp='C:\Users\Lucas\AntharesWork\openai-tunnel-client\tunnel-client.exe'
'TUNNEL_EXE='+[bool](Test-Path $tp)
if(Test-Path $tp){'TUNNEL_HELP_BEGIN'; & $tp --help 2>&1 | Select-Object -First 120; 'TUNNEL_HELP_END'}
'RUNNER='+[bool](Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue)
'TASKS_BEGIN'
Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {$_.TaskName -like '*Secure MCP Tunnel*' -or $_.TaskName -like '*Anthares*'} | ForEach-Object {[pscustomobject]@{TaskName=$_.TaskName;State=$_.State;Actions=@($_.Actions|ForEach-Object{[pscustomobject]@{Execute=$_.Execute;Arguments=$_.Arguments;WorkingDirectory=$_.WorkingDirectory}})}} | ConvertTo-Json -Depth 5 -Compress
'TASKS_END'
""".strip()
        job=_enqueue("shell",{"command":command,"shell":"powershell"},90)
        return jsonify(job_id=job["id"],status="queued"),202

    @app.post("/v1/bootstrap/tunnel-details")
    def tunnel_details():
        if not _authorized(): return jsonify(error="unauthorized"),401
        command=r"""
$ErrorActionPreference='Continue'
$tp='C:\Users\Lucas\AntharesWork\openai-tunnel-client\tunnel-client.exe'
if(-not(Test-Path $tp)){throw 'tunnel_client_missing'}
'QUICKSTART_BEGIN'; & $tp help quickstart 2>&1 | Select-Object -First 180; 'QUICKSTART_END'
'INIT_HELP_BEGIN'; & $tp init --help 2>&1 | Select-Object -First 180; 'INIT_HELP_END'
'PROFILES_BEGIN'; & $tp profiles list 2>&1 | Select-Object -First 120; 'PROFILES_END'
'ADMIN_HELP_BEGIN'; & $tp admin --help 2>&1 | Select-Object -First 120; 'ADMIN_HELP_END'
'SCRIPTS_BEGIN'
$files=@('C:\Users\Lucas\AntharesWork\openai-tunnel-client\start-meshcentral-tunnel.ps1','C:\Users\Lucas\AntharesWork\openai-tunnel-client\start-winremote-tunnel.ps1')
foreach($f in $files){if(Test-Path $f){'FILE='+$f; $raw=Get-Content $f -Raw; $raw=$raw -replace '(?i)(sk-[A-Za-z0-9_\-]{8,})','<REDACTED_KEY>'; $raw=$raw -replace '(?im)(CONTROL_PLANE_API_KEY\s*=\s*)[^\r\n]+','$1<REDACTED>'; $raw}}
'SCRIPTS_END'
""".strip()
        job=_enqueue("shell",{"command":command,"shell":"powershell"},90)
        return jsonify(job_id=job["id"],status="queued"),202

    @app.post("/v1/bootstrap/install-mcp")
    def install_mcp():
        if not _authorized(): return jsonify(error="unauthorized"),401
        token=os.getenv("ARA_SHARED","")
        if not token: return jsonify(error="control_secret_missing"),503
        token_b64=base64.b64encode(token.encode()).decode()
        command=(r"""
$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteMCP'
$repo=Join-Path $root 'repo'
New-Item -ItemType Directory -Force -Path $root | Out-Null
if(Test-Path $repo){Remove-Item -Recurse -Force $repo}
git clone --depth 1 --branch feature/anthares-remote-agent https://github.com/UniversoAnthares/anthares-kwai-runner.git $repo
$src=Join-Path $repo 'anthares-remote-mcp'
Push-Location $src
try { npm install --omit=dev } finally { Pop-Location }
$secret=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__TOKEN_B64__'))
$launcher=Join-Path $root 'start-local.ps1'
$lines=@('$env:ANTHARES_CONTROL_URL=''https://anthares-remote-control.onrender.com''','$env:ANTHARES_DEVICE_ID=''DESKTOP-FTDK0HP''',('$env:ARA_SHARED='''+$secret.Replace("'","''")+''''),('Set-Location '''+$src.Replace("'","''")+''''),'& node server.mjs')
Set-Content -Path $launcher -Value $lines -Encoding UTF8
icacls $launcher /inheritance:r /grant:r "$env:USERNAME`:F" | Out-Null
'INSTALL_MCP=OK'; 'PATH='+$src; 'PACKAGE_JSON='+[bool](Test-Path (Join-Path $src 'package.json')); 'NODE_MODULES='+[bool](Test-Path (Join-Path $src 'node_modules'))
""".strip()).replace('__TOKEN_B64__',token_b64)
        job=_enqueue("shell",{"command":command,"shell":"powershell"},120)
        return jsonify(job_id=job["id"],status="queued"),202

    @app.post("/v1/bootstrap/recover-runner")
    def recover_runner():
        if not _authorized(): return jsonify(error="unauthorized"),401
        command=r"""$ErrorActionPreference='Stop'; $root='C:\actions-runner'; if(-not(Test-Path (Join-Path $root 'run.cmd'))){throw 'runner_not_installed'}; $p=Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue; if(-not $p){Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','run.cmd' -WorkingDirectory $root -WindowStyle Hidden; Start-Sleep -Seconds 6}; $p=Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue; if($p){'RUNNER=ONLINE';'PID='+(($p|Select-Object -First 1).Id)}else{throw 'runner_not_started'}"""
        job=_enqueue("shell",{"command":command,"shell":"powershell"},30)
        return jsonify(job_id=job["id"],status="queued"),202

    @app.get("/v1/bootstrap/job/<job_id>")
    def job_status(job_id):
        if not _authorized(): return jsonify(error="unauthorized"),401
        if _ALLOWED.get(job_id,0)<time.time(): _ALLOWED.pop(job_id,None); return jsonify(error="not_found"),404
        with _relay._LOCK:
            state=_relay._DEVICES.setdefault(_DEVICE,{"heartbeat":None,"queue":[],"jobs":{}}); job=state["jobs"].get(job_id)
            if not job:return jsonify(error="not_found"),404
            result=job.get("result") or {}; return jsonify(status=job.get("status"),ok=result.get("ok"),output=result.get("output"),error=result.get("error"))
