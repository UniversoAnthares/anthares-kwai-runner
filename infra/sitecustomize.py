"""No application routes are registered implicitly at Python startup.

The ARA canary registers its authenticated routes only through ara_canary_app.
The production X worker registers its Runtime Mesh explicitly in its own
entrypoint. Keeping this module inert prevents an ARA canary from importing or
changing a pre-existing production worker.
"""
