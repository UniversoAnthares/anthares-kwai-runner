"""Expose truthful runtime durability metadata without changing the control API contract."""
import os


def backend_name():
    if os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return "postgres"
    if os.getenv("ARA_ALLOW_VOLATILE", "") == "1":
        return "volatile-memory"
    return "unavailable"


def register(app):
    @app.after_request
    def ara_runtime_truth(response):
        from flask import request
        if request.path != "/v1/control/capabilities" or response.status_code != 200 or not response.is_json:
            return response
        data = response.get_json(silent=True) or {}
        backend = backend_name()
        data["durability"] = backend
        data["durable_restart_recovery"] = backend == "postgres"
        response.set_data(app.json.dumps(data))
        response.content_type = "application/json"
        return response
