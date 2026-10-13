"""Explicit Anthares Remote Agent canary entrypoint.

Unlike sitecustomize.py, this module is imported directly by Gunicorn, so ARA route
registration does not depend on interpreter startup path behavior.
"""
import os

import x_render_worker_v3 as _worker
import anthares_remote_control_routes as _relay
from ara_legacy_state_compat import DevicesProxy

app = _worker.app
_relay._DEVICES = DevicesProxy(_relay)
_relay.register(app, os.getenv("ARA_SHARED", ""))

from anthares_remote_browser_bridge import register as _register_browser
from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap

# Deliberately do not register anthares_remote_bootstrap or anthares_remote_switch:
# both legacy modules expose shell-producing actions without controller authentication.
_register_browser(app)
_register_secure_bootstrap(app)
