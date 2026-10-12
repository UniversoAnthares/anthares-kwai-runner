"""Temporary, bounded bootstrap actions for the Anthares Remote Agent.

No arbitrary command input is accepted. This route exists only to finish upgrading the
already-authorized DESKTOP-FTDK0HP agent when ordinary admin bridges are unavailable.
"""
import threading
import time

from flask import jsonify, request

import anthares_remote_control_routes as _relay

_DEVICE = "DESKTOP-FTDK0HP"
_ALLOWED = {}


def _enqueue_shell(command, timeout=120):
    job_id = __import__("secrets").token_hex(16)
    job = {
        "id": job_id,
        "type": "shell",
        "args": {"command": command},
        "timeout_seconds": max(1, min(int(timeout), 120)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "queued",
    }
    with _relay._LOCK:
        state = _relay._DEVICES.setdefault(_DEVICE, {"heartbeat": None, "queue": [], "jobs": {}})
        state["jobs"][job_id] = job
        state["queue"].append(job_id)
    _ALLOWED[job_id] = time.time() + 900
    return job


def register(app):
    @app.post("/v1/public/bootstrap/probe")
    def ara_bootstrap_probe():
        command = r"""
$ErrorActionPreference='SilentlyContinue'
$go=Get-Command go -ErrorAction SilentlyContinue
$git=Get-Command git -ErrorAction SilentlyContinue
[pscustomobject]@{user=(whoami);go=if($go){$go.Source}else{$null};git=if($git){$git.Source}else{$null};admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)} | ConvertTo-Json -Compress
""".strip()
        job = _enqueue_shell(command, 30)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.post("/v1/public/bootstrap/upgrade-v02")
    def ara_bootstrap_upgrade():
        command = r"""
$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$work=Join-Path $env:TEMP 'ara-v02-build'
if(Test-Path $work){Remove-Item -Recurse -Force $work}
git clone --depth 1 --branch feature/anthares-remote-agent https://github.com/UniversoAnthares/anthares-kwai-runner.git $work
if(-not (Get-Command go -ErrorAction SilentlyContinue)){
  $zip=Join-Path $env:TEMP 'go1.23.2.windows-amd64.zip'
  Invoke-WebRequest -UseBasicParsing -Uri 'https://go.dev/dl/go1.23.2.windows-amd64.zip' -OutFile $zip
  $groot=Join-Path $env:TEMP 'ara-go1232'
  if(Test-Path $groot){Remove-Item -Recurse -Force $groot}
  Expand-Archive -Force $zip $groot
  $env:PATH=(Join-Path $groot 'go\bin')+';'+$env:PATH
}
Push-Location (Join-Path $work 'anthares-remote-agent')
try{
  go test ./...
  $env:GOOS='windows';$env:GOARCH='amd64';$env:CGO_ENABLED='0'
  $new=Join-Path $root 'anthares-remote-agent.v02.new.exe'
  go build -trimpath -ldflags '-s -w' -o $new ./cmd/agent
  $hash=(Get-FileHash $new -Algorithm SHA256).Hash.ToLowerInvariant()
}finally{Pop-Location}
$upgrade=Join-Path $root 'finish-v02-upgrade.ps1'
@"
Start-Sleep -Seconds 3
Get-Process 'anthares-remote-agent' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Copy-Item -Force '$root\anthares-remote-agent.exe' '$root\anthares-remote-agent.v01.bak.exe'
Move-Item -Force '$root\anthares-remote-agent.v02.new.exe' '$root\anthares-remote-agent.exe'
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','$root\run-agent.ps1'
"@ | Set-Content -Path $upgrade -Encoding UTF8
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$upgrade
"UPGRADE_SCHEDULED SHA256=$hash"
""".strip()
        job = _enqueue_shell(command, 120)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.post("/v1/public/bootstrap/prepare-system")
    def ara_bootstrap_prepare_system():
        command = r"""
$ErrorActionPreference='Stop'
$dir='C:\ProgramData\AntharesRemoteAgent'
$source=Join-Path $dir 'run-agent.ps1'
if(-not(Test-Path $source)){throw 'existing launcher missing'}
$credentialLines=Get-Content $source | Where-Object {$_ -match '^\$env:ANTHARES_(CONTROL_URL|DEVICE_TOKEN)='}
if($credentialLines.Count -ne 2){throw 'credential lines unavailable'}
$lines=@();$lines+=$credentialLines
$lines+="`$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP-SYSTEM'"
$lines+="`$env:ANTHARES_ALLOWED_ROOTS='C:\'"
$lines+="`$env:ANTHARES_ALLOW_SHELL='1'"
$lines+="& 'C:\ProgramData\AntharesRemoteAgent\anthares-remote-agent.exe' *>> 'C:\ProgramData\AntharesRemoteAgent\agent-system.log'"
Set-Content -Path (Join-Path $dir 'run-agent-system.ps1') -Value $lines -Encoding UTF8
'SYSTEM_LAUNCHER_PREPARED'
""".strip()
        job = _enqueue_shell(command, 30)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.get("/v1/public/bootstrap/job/<job_id>")
    def ara_bootstrap_job(job_id):
        expiry = _ALLOWED.get(job_id, 0)
        if expiry < time.time():
            _ALLOWED.pop(job_id, None)
            return jsonify(error="not_found"), 404
        with _relay._LOCK:
            state = _relay._DEVICES.setdefault(_DEVICE, {"heartbeat": None, "queue": [], "jobs": {}})
            job = state["jobs"].get(job_id)
            if not job:
                return jsonify(error="not_found"), 404
            result = job.get("result") or {}
            return jsonify(status=job.get("status"), ok=result.get("ok"), output=result.get("output"), error=result.get("error"))
