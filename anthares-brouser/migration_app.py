from base_app import app
from migration_capsule import router as migration_router

app.include_router(migration_router)
