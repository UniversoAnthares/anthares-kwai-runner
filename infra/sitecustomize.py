"""ARA does not register routes implicitly during interpreter startup.

The dedicated service must start with `gunicorn --chdir infra ara_canary_app:app`.
Implicit registration via sitecustomize could double-register routes when that explicit
entrypoint imports the existing worker, and could affect unrelated production workers.
"""
