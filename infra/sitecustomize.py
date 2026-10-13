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
    # This eliminates the legacy per-process MCP queue without changing the
    # Ed25519 request-verification contract.
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
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)
    from ara_install_probe import register as _register_install_probe
    _register_install_probe(_worker.app)
    from anthares_runtime_mesh_vaulted import register as _register_runtime_mesh
    _register_runtime_mesh(_worker.app)

    # Deliberately omitted: anthares_remote_bootstrap. Its public routes enqueue shell
    # jobs without controller authentication and are not safe for a public service.
except Exception as _exc:
    # Never print configuration values or request data; only the exception class and bounded message.
    print("ARA_BOOTSTRAP_ERROR=" + type(_exc).__name__ + ":" + str(_exc)[:240], flush=True)
