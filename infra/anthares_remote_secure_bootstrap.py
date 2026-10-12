"""Ephemeral, challenge-authenticated bootstrap actions for Anthares Remote.

This bridge accepts no caller-supplied shell commands. It exists only to finish wiring the
user-owned MCP transport while the normal admin bridges are unavailable.
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


def _enqueue(job_type, args=None, timeout=60):
    job_id = secrets.token_hex(16)
    job = {
        "id": job_id,
        "type": job_type,
        "args": args or {},
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
    @app.post("/v1/bootstrap/diagnose")
    def ara_secure_diagnose():
        if not _authorized():
            return jsonify(error="unauthorized"), 401
        command = r"""
$ErrorActionPreference='Continue'
'WHO=' + (whoami)
$node=Get-Command node -ErrorAction SilentlyContinue
'NODE=' + [bool]$node
if($node){node --version}
$npm=Get-Command npm -ErrorAction SilentlyContinue
'NPM=' + [bool]$npm
$t=Get-Command tunnel-client -ErrorAction SilentlyContinue
'TUNNEL_CLIENT=' + [bool]$t
if($t){'TUNNEL_PATH=' + $t.Source; tunnel-client --version 2>$null; tunnel-client --help 2>$null | Select-Object -First 80}
'RUNNER=' + [bool](Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue)
Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {$_.TaskName -like '*Secure MCP Tunnel*' -or $_.TaskName -like '*Anthares*'} | Select-Object TaskName,State | ConvertTo-Json -Compress
""".strip()
        job = _enqueue("shell", {"command": command, "shell": "powershell"}, 45)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.post("/v1/bootstrap/recover-runner")
    def ara_secure_recover_runner():
        if not _authorized():
            return jsonify(error="unauthorized"), 401
        command = r"""
$ErrorActionPreference='Stop'
$root='C:\actions-runner'
if(-not(Test-Path (Join-Path $root 'run.cmd'))){throw 'runner_not_installed'}
$p=Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue
if(-not $p){Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','run.cmd' -WorkingDirectory $root -WindowStyle Hidden; Start-Sleep -Seconds 6}
$p=Get-Process 'Runner.Listener' -ErrorAction SilentlyContinue
if($p){'RUNNER=ONLINE';'PID='+(($p|Select-Object -First 1).Id)}else{throw 'runner_not_started'}
""".strip()
        job = _enqueue("shell", {"command": command, "shell": "powershell"}, 30)
        return jsonify(job_id=job["id"], status="queued"), 202

    @app.get("/v1/bootstrap/job/<job_id>")
    def ara_secure_job(job_id):
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
