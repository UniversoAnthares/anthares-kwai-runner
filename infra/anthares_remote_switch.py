"""One-shot bounded migration of the Anthares agent to its dedicated Render service."""
import secrets
import time
from flask import jsonify
import anthares_remote_control_routes as _relay

_DEVICE = "DESKTOP-FTDK0HP"
_TARGET = "https://anthares-remote-control.onrender.com"
_JOBS = {}


def _enqueue(command):
    job = _relay.enqueue_job(_DEVICE, "shell", {"command": command}, 30)
    _JOBS[job["id"]] = time.time() + 300
    return job["id"]

def register(app):
    @app.post("/v1/public/bootstrap/switch-dedicated")
    def ara_switch_dedicated():
        command = r"""
$ErrorActionPreference='Stop'
$dir='C:\ProgramData\AntharesRemoteAgent'
$launcher=Join-Path $dir 'run-agent.ps1'
if(-not(Test-Path $launcher)){throw 'launcher_missing'}
$lines=Get-Content $launcher
$found=$false
$new=@()
foreach($line in $lines){
  if($line -match '^\$env:ANTHARES_CONTROL_URL='){
    $new += '$env:ANTHARES_CONTROL_URL=''https://anthares-remote-control.onrender.com'''
    $found=$true
  } else { $new += $line }
}
if(-not $found){throw 'control_url_line_missing'}
Set-Content -Path $launcher -Value $new -Encoding UTF8
$verify=(Get-Content $launcher | Where-Object {$_ -match '^\$env:ANTHARES_CONTROL_URL='} | Select-Object -First 1)
if($verify -ne '$env:ANTHARES_CONTROL_URL=''https://anthares-remote-control.onrender.com'''){throw 'launcher_verify_failed'}
$restart=Join-Path $dir 'switch-control-restart.ps1'
$restartLines=@(
  'Start-Sleep -Seconds 4',
  'Get-Process ''anthares-remote-agent'' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue',
  'Start-Sleep -Seconds 2',
  'Start-Process powershell.exe -WindowStyle Hidden -ArgumentList ''-NoProfile'',''-ExecutionPolicy'',''Bypass'',''-File'',''C:\ProgramData\AntharesRemoteAgent\run-agent.ps1'''
)
Set-Content -Path $restart -Value $restartLines -Encoding UTF8
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$restart
'MIGRATION_SCHEDULED'
'CONTROL_URL='+$verify
""".strip()
        job_id=_enqueue(command)
        return jsonify(job_id=job_id,status="queued"),202

    @app.get("/v1/public/bootstrap/switch-job/<job_id>")
    def ara_switch_job(job_id):
        if _JOBS.get(job_id,0)<time.time(): return jsonify(error="not_found"),404
        job = _relay.get_job(_DEVICE, job_id)
        if not job: return jsonify(error="not_found"), 404
        result = job.get("result") or {}
        return jsonify(status=job.get("status"), ok=result.get("ok"), output=result.get("output"), error=result.get("error"))
