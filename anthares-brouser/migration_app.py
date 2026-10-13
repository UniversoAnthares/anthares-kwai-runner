from base_app import app
from migration_capsule import router as migration_router
from migration_oidc import router as migration_oidc_router

app.include_router(migration_router)
app.include_router(migration_oidc_router)
