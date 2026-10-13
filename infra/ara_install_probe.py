"""Fixed, challenge-authenticated ARA installation diagnostic.

No caller-supplied command is accepted and no credential file contents are returned.
"""
import os
import secrets
import time

from flask import jsonify, request

import anthares_remote_control_routes as _relay

_DEVICE = "DESKTOP-FTDK0HP"
_ALLOWED = {}


def _authorized():
    supplied = request.headers.get("X-Anthares-Bootstrap", "")
    expected = os.getenv("ARA_BROWSER_APPROVED_CHALLENGE", "")
    return bool(supplied and expected) and secrets.compare_digest(supplied, expected)


def _enqueue(command, timeout=30):
    job_id = secrets.token_hex(16)
    job = {
        "id": job_id,
        "type": "shell",
        "args": {"command": command, "shell": "powershell"},
        "timeout_seconds": max(1, min(int(timeout), 120)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "queued",
    }
    with _relay._LOCK:
        state = _relay._DEVICES.setdefault(_DEVICE, {"heartbeat": None, "queue": [], "jobs": {}})
        state["jobs"][job_id] = job
        state["queue"].append(job_id)
    _ALLOWED[job_id] = time.time() + 300
    return job


def register(app):
    @app.get("/v1/bootstrap/ara-install-proof")
    def ara_install_proof():
        if not _authorized():
            return jsonify(error="unauthorized"), 401
        command = r"""
$ErrorActionPreference='SilentlyContinue'
$root='C:\ProgramData\AntharesRemoteAgent'
$exe=Join-Path $root 'anthares-remote-agent.exe'
$launcher=Join-Path $root 'run-agent.ps1'
$report=Join-Path $root 'install-report.txt'
$startup=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\AntharesRemoteAgent.cmd'
$ps=@(Get-Process 'anthares-remote-agent' -ErrorAction SilentlyContinue)
$path=$null
if($ps.Count -gt 0){$path=$ps[0].Path}
$hash=$null
if(Test-Path $exe){$hash=(Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()}
$reportSafe=@()
if(Test-Path $report){$reportSafe=@(Get-Content $report | Where-Object {$_ -match '^(INSTALL|EXE_SHA256|PID|STARTUP|DEVICE_HASH_PUBLISHED)='})}
[pscustomobject]@{
  user=(whoami)
  process_count=$ps.Count
  process_path=$path
  exe_exists=[bool](Test-Path $exe)
  exe_sha256=$hash
  launcher_exists=[bool](Test-Path $launcher)
  startup_exists=[bool](Test-Path $startup)
  install_report_exists=[bool](Test-Path $report)
  install_report_safe=$reportSafe
} | ConvertTo-Json -Depth 4 -Compress
""".strip()
        job = _enqueue(command, 30)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.get("/v1/bootstrap/ara-install-proof/job/<job_id>")
    def ara_install_proof_job(job_id):
        if not _authorized():
            return jsonify(error="unauthorized"), 401
        if _ALLOWED.get(job_id, 0) < time.time():
            _ALLOWED.pop(job_id, None)
            return jsonify(error="not_found"), 404
        with _relay._LOCK:
            state = _relay._DEVICES.setdefault(_DEVICE, {"heartbeat": None, "queue": [], "jobs": {}})
            job = state["jobs"].get(job_id)
            if not job:
                return jsonify(error="not_found"), 404
            result = job.get("result") or {}
            return jsonify(status=job.get("status"), ok=result.get("ok"), output=result.get("output"), error=result.get("error"))
