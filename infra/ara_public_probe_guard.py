"""Fail-closed protection for optional public ARA diagnostics."""
import os
import secrets

from flask import jsonify, request


def register(app):
    @app.before_request
    def ara_public_probe_guard():
        if not request.path.startswith('/v1/public/'):
            return None
        expected = os.getenv('ARA_PROBE_TOKEN', '')
        supplied = request.headers.get('X-Anthares-Probe', '')
        if not expected:
            return jsonify(error='not_found'), 404
        if not supplied or not secrets.compare_digest(supplied, expected):
            return jsonify(error='unauthorized'), 401
        return None
