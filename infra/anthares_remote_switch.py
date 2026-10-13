"""Retired one-shot Anthares Remote migration bridge.

The Windows agent has been cut over to the dedicated PostgreSQL-backed controller.
Keep this module as a harmless compatibility import for existing bootstraps, but expose
no public migration or job-status routes.
"""


def register(app):
    return None
