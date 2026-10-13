"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    from ara_public_probe_guard import register as _register_probe_guard
    from anthares_remote_control_routes import register as _register_remote

    _register_probe_guard(_worker.app)
    _register_remote(_worker.app, _os.getenv("ARA_SHARED", ""))

    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)
    from ara_install_probe import register as _register_install_probe
    _register_install_probe(_worker.app)
    from anthares_runtime_mesh import register as _register_runtime_mesh
    _register_runtime_mesh(_worker.app)

    # Deliberately omitted: anthares_remote_bootstrap. Its public routes enqueue shell
    # jobs without controller authentication and are not safe for a public service.
except Exception:
    # Keep the existing X worker boot path fail-open; deployment logs will expose errors.
    pass
