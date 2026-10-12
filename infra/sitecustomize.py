"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    from anthares_remote_control_routes import register as _register_remote
    _register_remote(_worker.app, _os.getenv("ARA_SHARED", ""))
    from anthares_remote_bootstrap import register as _register_bootstrap
    _register_bootstrap(_worker.app)
    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_switch import register as _register_switch
    _register_switch(_worker.app)
except Exception:
    # Keep the existing X worker boot path fail-open; deployment logs will expose errors.
    pass
