"""One-shot bounded migration of the Anthares agent to its dedicated Render service."""
import secrets
import time
from flask import jsonify
import anthares_remote_control_routes as _relay

_DEVICE = "DESKTOP-FTDK0HP"
_TARGET = "https://anthares-remote-control.onrender.com"
_JOBS = {}


def _enqueue(command):
    job_id = secrets.token_hex(16)
    job = {"id":job_id,"type":"shell","args":{"command":command},"timeout_seconds":30,"created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"status":"queued"}
    with _relay._LOCK:
        s=_relay._DEVICES.setdefault(_DEVICE,{"heartbeat":None,"queue":[],"jobs":{}})
        s["jobs"][job_id]=job; s["queue"].append(job_id)
    _JOBS[job_id]=time.time()+300
    return job_id


def register(app):
    @app.post("/v1/public/bootstrap/switch-dedicated")
    def ara_switch_dedicated():
        command = r"""
$ErrorActionPreference='Stop'
$dir='C:\ProgramData\AntharesRemoteAgent'
$launcher=Join-Path $dir 'run-agent.ps1'
$text=Get-Content $launcher -Raw
$text=[regex]::Replace($text,"(?m)^\$env:ANTHARES_CONTROL_URL='[^']*'","`$env:ANTHARES_CONTROL_URL='https://anthares-remote-control.onrender.com'")
Set-Content -Path $launcher -Value $text -Encoding UTF8
$restart=Join-Path $dir 'switch-control-restart.ps1'
@"
Start-Sleep -Seconds 3
Get-Process 'anthares-remote-agent' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','C:\ProgramData\AntharesRemoteAgent\run-agent.ps1'
"@ | Set-Content -Path $restart -Encoding UTF8
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$restart
'MIGRATION_SCHEDULED TARGET=https://anthares-remote-control.onrender.com'
""".strip()
        job_id=_enqueue(command)
        return jsonify(job_id=job_id,status="queued"),202

    @app.get("/v1/public/bootstrap/switch-job/<job_id>")
    def ara_switch_job(job_id):
        if _JOBS.get(job_id,0)<time.time(): return jsonify(error="not_found"),404
        with _relay._LOCK:
            job=_relay._DEVICES.setdefault(_DEVICE,{"heartbeat":None,"queue":[],"jobs":{}})["jobs"].get(job_id)
            if not job:return jsonify(error="not_found"),404
            result=job.get("result") or {}
            return jsonify(status=job.get("status"),ok=result.get("ok"),output=result.get("output"),error=result.get("error"))
