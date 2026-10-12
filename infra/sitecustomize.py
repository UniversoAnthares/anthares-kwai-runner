"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import x_render_worker_v3 as _worker
    from anthares_remote_control_routes import register as _register_remote
    _register_remote(_worker.app, _worker.TOKEN)
except Exception:
    # Keep the existing X worker boot path fail-open; deployment logs will expose errors.
    pass
