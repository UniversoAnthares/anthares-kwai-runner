"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    import anthares_remote_control_routes as _relay
    from ara_public_probe_guard import register as _register_probe_guard
    from ara_runtime_truth import register as _register_runtime_truth

    _register_probe_guard(_worker.app)
    _register_runtime_truth(_worker.app)
    _relay.register(_worker.app, _os.getenv("ARA_SHARED", ""))

    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)

    # Intentionally omitted: anthares_remote_bootstrap and anthares_remote_switch.
    # Their legacy public endpoints enqueue shell-producing actions without controller auth.
except Exception:
    # Never advertise a running ARA service with silently missing security routes.
    # The dedicated canary uses ara_canary_app:app for explicit initialization.
    import logging
    logging.getLogger("anthares.ara").exception("ARA route registration failed")
    raise
