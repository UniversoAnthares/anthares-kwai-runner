"""Co-host durable ARA control and the Render-independent X worker on one Northflank service."""
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware

os.environ.setdefault("ANTHARES_BROWSER_STATE_AUTHORITY", "runtime")
os.environ.setdefault(
    "ANTHARES_BROWSER_STATE_VAULT_URL",
    "https://anthares-x-vault.anthares1.workers.dev/browser-state/runtime",
)

from ara_canary_app import app as ara_app
from x_runtime_worker import app as x_app

# ARA keeps its existing root API. X is isolated under /x and shares the
# durable Cloudflare browser-state vault plus the existing Northflank process.
app = DispatcherMiddleware(ara_app, {"/x": x_app})
