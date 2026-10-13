"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker
    import anthares_remote_control_routes as _relay
    from ara_legacy_state_compat import DevicesProxy as _DevicesProxy

    # Legacy bootstrap modules still reference _DEVICES directly. This proxy maps those
    # writes/reads to the durable store while their public contracts remain unchanged.
    _relay._DEVICES = _DevicesProxy(_relay)

    _relay.register(_worker.app, _os.getenv("ARA_SHARED", ""))
    from anthares_remote_bootstrap import register as _register_bootstrap
    _register_bootstrap(_worker.app)
    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_switch import register as _register_switch
    _register_switch(_worker.app)
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)
except Exception:
    # Keep the existing X worker boot path fail-open; deployment logs will expose errors.
    pass
