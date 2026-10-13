"""Do not register ARA routes implicitly during interpreter startup.

The dedicated ARA service uses ``gunicorn --chdir infra ara_canary_app:app``.
Keeping this module inert prevents double route registration and ensures that the
canary neither changes nor depends on any pre-existing Render worker integration.
The runtime-mesh module remains available to its owning worker; this ARA branch
does not activate it as a side effect of importing Python's sitecustomize.
"""
