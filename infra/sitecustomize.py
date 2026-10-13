"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    import anthares_remote_control_routes as _relay
    from ara_legacy_state_compat import DevicesProxy as _DevicesProxy
    from ara_public_probe_guard import register as _register_probe_guard

    _register_probe_guard(_worker.app)

    # Secure bootstrap still uses the legacy state shape; map that shape to the durable store.
    _relay._DEVICES = _DevicesProxy(_relay)

    _relay.register(_worker.app, _os.getenv("ARA_SHARED", ""))
    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)

    # Intentionally omitted: anthares_remote_bootstrap and anthares_remote_switch.
    # Their legacy public endpoints enqueue shell-producing actions without controller auth.
except Exception:
    # Keep the existing X worker boot path fail-open; deployment logs will expose errors.
    pass
