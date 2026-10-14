"""Retired Anthares Remote bootstrap surface.

Phase 4 now has a single canonical installation path:
C:\\ProgramData\\AntharesRemoteAgent, SYSTEM/session 0, private issue queues,
and local watchdog recovery.  The former bootstrap endpoints could recreate the
legacy HTTP/user-session topology, so they are deliberately non-operational.
"""

from flask import jsonify

_RETIREMENT = {
    "error": "retired",
    "replacement": "anthares-remote-agent/windows/install-system-v8.ps1",
    "canonical_install_root": r"C:\ProgramData\AntharesRemoteAgent",
    "canonical_executor": "SYSTEM/session-0",
    "canonical_transport": "private-issue-queues",
    "render_required": False,
}


def register(app):
    def retired():
        return jsonify(**_RETIREMENT), 410

    app.add_url_rule("/v1/public/bootstrap/probe", "ara_bootstrap_probe_retired", retired, methods=["POST"])
    app.add_url_rule("/v1/public/bootstrap/upgrade-v02", "ara_bootstrap_upgrade_retired", retired, methods=["POST"])
    app.add_url_rule("/v1/public/bootstrap/prepare-system", "ara_bootstrap_prepare_system_retired", retired, methods=["POST"])

    @app.get("/v1/public/bootstrap/job/<job_id>")
    def ara_bootstrap_job_retired(job_id):
        return jsonify(**_RETIREMENT), 410
