"""Register Anthares Remote Agent relay routes when this Render service starts."""
try:
    import os as _os
    import x_render_worker_v3 as _worker

    # Recovery-only escape hatch for the legacy X-hosted control surface. It is
    # opt-in per service and never overrides the durable production controller.
    # This lets an already-installed Windows agent receive one bounded migration
    # job even when an unrelated DATABASE_URL exists on the X worker.
    if _os.getenv("ARA_FORCE_VOLATILE", "") == "1":
        import ara_state_store as _ara_state
        _ara_state.build_store = lambda: _ara_state.MemoryStore()

    from anthares_remote_control_routes import register as _register_remote
    _register_remote(_worker.app, _os.getenv("ARA_SHARED", ""))
    from anthares_remote_bootstrap import register as _register_bootstrap
    _register_bootstrap(_worker.app)
    from anthares_remote_browser_bridge import register as _register_browser
    _register_browser(_worker.app)
    from anthares_remote_switch import register as _register_switch
    _register_switch(_worker.app)
    from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap
    _register_secure_bootstrap(_worker.app)
    # Register the vault-backed Anthares-browser adapter, which delegates to the
    # original runtime mesh when an external browser URL is configured and uses
    # the isolated local Playwright+vault backend otherwise.
    from anthares_runtime_mesh_vaulted import register as _register_runtime_mesh
    _register_runtime_mesh(_worker.app)
except Exception:
    # Keep the X worker boot path available, but never hide a broken runtime integration.
    import logging as _logging
    _logging.getLogger("anthares.runtime.startup").exception("Anthares runtime integration registration failed")
    if _os.getenv("ANTHARES_REQUIRE_RUNTIME_MESH", "0") == "1":
        raise
