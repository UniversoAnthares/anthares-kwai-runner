"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    from ara_public_probe_guard import register as _register_probe_guard
    import anthares_remote_control_routes as _relay

    _register_probe_guard(_worker.app)
    _relay.register(_worker.app, _os.getenv("ARA_SHARED", ""))

    # Keep the signed MCP surface, but route its status/enqueue/execute helpers
    # through the same durable store used by the controller/device endpoints.
    import anthares_remote_mcp_bridge as _mcp_bridge

    def _durable_status(device):
        status = dict(_relay.device_status(device))
        status["state_backend"] = type(_relay._store()).__name__
        return status

    _mcp_bridge._status = _durable_status
    _mcp_bridge._enqueue = lambda device, job_type, args=None, timeout=30: _relay.enqueue_job(
        device, job_type, args or {}, timeout
    )
    _mcp_bridge._execute = lambda device, job_type, args=None, timeout=30: _relay.execute_job(
        device, job_type, args or {}, timeout
    )
    _mcp_bridge.register(_worker.app)

    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)

    # The historical secure-bootstrap module still targets the pre-store
    # in-memory queue. Keep it out of the production registration path.
    # A bounded migration is queued through the current store when explicitly
    # enabled for this rollout, so the Windows agent can move to PostgreSQL.
    if _os.getenv("ARA_MIGRATE_TO_DURABLE", "") == "1":
        _migration_command = r"""
$ErrorActionPreference='Stop'
$dir='C:\ProgramData\AntharesRemoteAgent'
$launcher=Join-Path $dir 'run-agent.ps1'
if(-not(Test-Path $launcher)){throw 'launcher_missing'}
$target='https://anthares-ara-control.onrender.com'
$lines=Get-Content $launcher
$found=$false
$new=@()
foreach($line in $lines){
  if($line -match '^\$env:ANTHARES_CONTROL_URL='){
    $new += ('$env:ANTHARES_CONTROL_URL='''+$target+'''')
    $found=$true
  } else { $new += $line }
}
if(-not $found){throw 'control_url_line_missing'}
$tmp=Join-Path $dir 'run-agent.ps1.new'
Set-Content -Path $tmp -Value $new -Encoding UTF8
$verify=(Get-Content $tmp | Where-Object {$_ -match '^\$env:ANTHARES_CONTROL_URL='} | Select-Object -First 1)
if($verify -ne ('$env:ANTHARES_CONTROL_URL='''+$target+'''')){throw 'launcher_verify_failed'}
Move-Item -Force $tmp $launcher
$restart=Join-Path $dir 'switch-durable-control.ps1'
$restartLines=@(
  'Start-Sleep -Seconds 3',
  'Get-Process ''anthares-remote-agent'' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue',
  'Start-Sleep -Seconds 2',
  'Start-Process powershell.exe -WindowStyle Hidden -ArgumentList ''-NoProfile'',''-ExecutionPolicy'',''Bypass'',''-File'',''C:\ProgramData\AntharesRemoteAgent\run-agent.ps1'''
)
Set-Content -Path $restart -Value $restartLines -Encoding UTF8
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$restart
'MIGRATION_SCHEDULED'
'CONTROL_URL='+$target
""".strip()
        _migration_job = _relay.enqueue_job(
            "DESKTOP-FTDK0HP", "shell", {"command": _migration_command, "shell": "powershell"}, 45
        )
        print("ARA_DURABLE_MIGRATION_QUEUED=" + str(_migration_job.get("id", "")), flush=True)

    from ara_install_probe import register as _register_install_probe
    _register_install_probe(_worker.app)
    from anthares_runtime_mesh_vaulted import register as _register_runtime_mesh
    _register_runtime_mesh(_worker.app)

    # Deliberately omitted: legacy public bootstrap modules. Their historic
    # queue assumptions are incompatible with the durable store and they are
    # unnecessary once the agent points at the dedicated PostgreSQL control.
except Exception as _exc:
    # Never print configuration values or request data; only the exception class and bounded message.
    print("ARA_BOOTSTRAP_ERROR=" + type(_exc).__name__ + ":" + str(_exc)[:240], flush=True)
