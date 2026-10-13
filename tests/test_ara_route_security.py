import os
import pathlib
import sys
import unittest
from unittest import mock

from flask import Flask

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))

import ara_public_probe_guard
import ara_runtime_truth
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

    def test_runtime_truth_reports_volatile_only_when_explicit(self):
        with mock.patch.dict(os.environ, {'ARA_ALLOW_VOLATILE': '1'}, clear=True):
            self.assertEqual(ara_runtime_truth.backend_name(), 'volatile-memory')

    def test_runtime_truth_reports_postgres_when_dsn_exists(self):
        with mock.patch.dict(os.environ, {'ARA_DATABASE_URL': 'postgresql://example.invalid/db'}, clear=True):
            self.assertEqual(ara_runtime_truth.backend_name(), 'postgres')

    def test_runtime_truth_reports_unavailable_without_backend(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ara_runtime_truth.backend_name(), 'unavailable')

    def test_device_result_rejects_unleased_job_at_http_boundary(self):
        import hashlib
        import anthares_remote_control_routes as relay
        from ara_state_store import MemoryStore
        app = Flask(__name__)
        token = "device-test-token"
        device = "TEST-DEVICE"
        store = MemoryStore()
        with mock.patch.object(relay, "_STORE", store), mock.patch.dict(
            os.environ, {"ARA_DEVICE_HASH_TEST_DEVICE": hashlib.sha256(token.encode()).hexdigest()}
        ):
            relay.register(app, "controller-token")
            job = store.enqueue(device, "ping", {})
            response = app.test_client().post(
                "/v1/device/jobs/" + job["id"] + "/result",
                json={"ok": True},
                headers={"Authorization": "Bearer " + token, "X-Anthares-Device": device},
            )
            self.assertEqual(response.status_code, 409)
            self.assertEqual(store.get_job(device, job["id"])["status"], "queued")

    def test_canary_healthz_checks_postgres_without_exposing_secrets(self):
        source = (ROOT / "infra" / "ara_canary_app.py").read_text(encoding="utf-8")
        self.assertIn('@app.get("/healthz")', source)
        self.assertIn('cursor.execute("SELECT 1")', source)
        self.assertIn('"backend": "postgres"', source)
        self.assertNotIn('"dsn":', source)

    def test_canary_requires_durable_database_and_controller_secret(self):
        source = (ROOT / 'infra' / 'ara_canary_app.py').read_text(encoding='utf-8')
        self.assertIn('if not os.getenv("ARA_SHARED"):', source)
        self.assertIn('if not (os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")):', source)
        self.assertIn('build_store()', source)

    def test_dedicated_canary_does_not_import_production_worker(self):
        source = (ROOT / 'infra' / 'ara_canary_app.py').read_text(encoding='utf-8')
        self.assertIn('app = Flask("anthares_remote_agent_canary")', source)
        self.assertNotIn('import x_render_worker_v3', source)

    def test_canary_entrypoint_does_not_register_legacy_bootstrap_modules(self):
        source = (ROOT / 'infra' / 'ara_canary_app.py').read_text(encoding='utf-8')
        self.assertNotIn('from anthares_remote_bootstrap import', source)
        self.assertNotIn('from anthares_remote_switch import', source)

    def test_production_worker_registers_runtime_mesh_without_sitecustomize(self):
        sitecustomize = (ROOT / 'infra' / 'sitecustomize.py').read_text(encoding='utf-8')
        worker = (ROOT / 'infra' / 'x_render_worker_v3.py').read_text(encoding='utf-8')
        self.assertNotIn('import x_render_worker_v3', sitecustomize)
        self.assertIn('from anthares_runtime_mesh import register', worker)


if __name__ == '__main__':
    unittest.main()
