"""Combined Northflank runtime after Render retirement.

Keep the durable ARA canary/controller at the service root and mount the X
browser worker under /x so one existing free Northflank service replaces the
last Render X worker without consuming another service slot.
"""
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from ara_canary_app import app as ara_app
from x_render_worker_v3 import app as x_app

app = DispatcherMiddleware(ara_app, {"/x": x_app})
