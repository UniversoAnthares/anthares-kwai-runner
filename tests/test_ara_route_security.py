import os
import pathlib
import sys
import unittest
from unittest import mock

from flask import Flask

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))

import ara_public_probe_guard
import anthares_remote_secure_bootstrap


class RouteSecurityTests(unittest.TestCase):
    def test_probe_guard_hides_public_routes_without_server_token(self):
        app = Flask(__name__)
        ara_public_probe_guard.register(app)

        @app.get('/v1/public/status')
        def status():
            return {'ok': True}

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ARA_PROBE_TOKEN', None)
            response = app.test_client().get('/v1/public/status')
        self.assertEqual(response.status_code, 404)

    def test_probe_guard_rejects_missing_or_wrong_probe_header(self):
        app = Flask(__name__)
        ara_public_probe_guard.register(app)

        @app.get('/v1/public/status')
        def status():
            return {'ok': True}

        with mock.patch.dict(os.environ, {'ARA_PROBE_TOKEN': 'test-probe-token'}):
            client = app.test_client()
            self.assertEqual(client.get('/v1/public/status').status_code, 401)
            self.assertEqual(client.get('/v1/public/status', headers={'X-Anthares-Probe': 'wrong'}).status_code, 401)
            self.assertEqual(client.get('/v1/public/status', headers={'X-Anthares-Probe': 'test-probe-token'}).status_code, 200)

    def test_secure_bootstrap_rejects_missing_challenge(self):
        app = Flask(__name__)
        anthares_remote_secure_bootstrap.register(app)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ARA_BROWSER_APPROVED_CHALLENGE', None)
            response = app.test_client().post('/v1/bootstrap/diagnose')
        self.assertEqual(response.status_code, 401)

    def test_canary_entrypoint_does_not_register_legacy_bootstrap_modules(self):
        source = (ROOT / 'infra' / 'ara_canary_app.py').read_text(encoding='utf-8')
        self.assertNotIn('from anthares_remote_bootstrap import', source)
        self.assertNotIn('from anthares_remote_switch import', source)

    def test_sitecustomize_does_not_register_legacy_bootstrap_modules(self):
        source = (ROOT / 'infra' / 'sitecustomize.py').read_text(encoding='utf-8')
        self.assertNotIn('from anthares_remote_bootstrap import', source)
        self.assertNotIn('from anthares_remote_switch import', source)


if __name__ == '__main__':
    unittest.main()
