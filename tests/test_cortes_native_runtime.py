"""Offline boundary regressions for the account-specific native runtime.
Run: python -m unittest discover -s tests -p test_cortes_native_runtime.py
Requires PyYAML. No credentials, network calls or publisher execution.
"""
import copy
import json
from pathlib import Path
import re
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ".github/workflows/cortes-tiktok-lucasrosalem4-cloud-publisher.yml",
    ".github/workflows/cortes-tiktok-lucasrosalem4-windows-fallback.yml",
)
SECRET = "CORTES_TIKTOK_LUCAS4_STORAGE_STATE"
VARIABLE = "TIKTOK_LUCASROSALEM4_STORAGE_STATE"
EXPRESSION = "${{ secrets." + SECRET + " }}"
ENVIRONMENT = "cortes-tiktok-lucas4"


def assert_boundary(document):
    """Offline workflow contract, never an attestation of provider permissions."""
    if document.get("env"):
        raise ValueError("global environment forbidden")
    if document.get("permissions") != {"contents": "read", "id-token": "write"}:
        raise ValueError("unexpected permissions")
    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or len(jobs) != 1:
        raise ValueError("expected one dedicated consumer")
    for job in jobs.values():
        if job.get("environment") != ENVIRONMENT:
            raise ValueError("wrong account environment")
        if VARIABLE in job.get("env", {}):
            raise ValueError("session exposed at job scope")
        steps = job.get("steps", [])
        if not steps or steps[0].get("env", {}).get(VARIABLE) != EXPRESSION:
            raise ValueError("credential gate must run first")
        gate = steps[0].get("run", "")
        if VARIABLE not in gate:
            raise ValueError("credential presence gate missing")
        credential_steps = []
        for index, step in enumerate(steps):
            env = step.get("env", {})
            if VARIABLE in env:
                credential_steps.append(index)
                if env[VARIABLE] != EXPRESSION:
                    raise ValueError("legacy or shared fallback")
            if str(step.get("uses", "")).startswith("actions/checkout@"):
                if step.get("with", {}).get("persist-credentials") is not False:
                    raise ValueError("checkout persists token")
            if index not in (0, len(steps)-1) and VARIABLE in env:
                raise ValueError("session exposed to dependency or test step")
        if credential_steps != [0, len(steps)-1]:
            raise ValueError("session must be limited to gate and publisher")
        if "cortes_tiktok_lucasrosalem4_cloud_publish.py" not in steps[-1].get("run", ""):
            raise ValueError("unexpected publisher")
    serialized = json.dumps(document)
    # Deny dynamic/indexed secret access, even when hidden in an unused field.
    if re.search(r"secrets\s*\[", serialized):
        raise ValueError("dynamic secret access forbidden")
    for expression in re.findall(r"\$\{\{[^}]*secrets[^}]*\}\}", serialized):
        if expression != EXPRESSION:
            raise ValueError("secret context or expression escape")
    refs = set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", serialized))
    if refs != {SECRET}:
        raise ValueError("foreign or missing secret")
    return True


class NativeRuntimeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = [yaml.safe_load((ROOT / p).read_text(encoding="utf-8")) for p in PATHS]

    def reject(self, mutate):
        for document in self.documents:
            with self.subTest(workflow=document["name"]):
                changed = copy.deepcopy(document)
                mutate(changed, next(iter(changed["jobs"].values())))
                with self.assertRaises(ValueError):
                    assert_boundary(changed)

    def test_prepared_consumers(self):
        for doc in self.documents:
            self.assertTrue(assert_boundary(doc))

    def test_wrong_environment(self):
        self.reject(lambda d, j: j.update(environment="cortes-instagram"))

    def test_missing_environment(self):
        self.reject(lambda d, j: j.pop("environment"))

    def test_job_session_exposure(self):
        self.reject(lambda d, j: j.setdefault("env", {}).update({VARIABLE: EXPRESSION}))

    def test_dependency_session_exposure(self):
        self.reject(lambda d, j: j["steps"][1].setdefault("env", {}).update({VARIABLE: EXPRESSION}))

    def test_foreign_provider_secret(self):
        self.reject(lambda d, j: j["steps"][-1].setdefault("env", {}).update(
            {"FOREIGN": "${{ secrets.INSTAGRAM_ACCESS_TOKEN }}"}))

    def test_shared_bws_fallback(self):
        self.reject(lambda d, j: j["steps"][-1]["env"].update(
            {VARIABLE: EXPRESSION[:-3] + " || secrets.BWS_ACCESS_TOKEN }}"}))

    def test_global_secret_exposure(self):
        self.reject(lambda d, j: d.update(env={VARIABLE: EXPRESSION}))

    def test_checkout_persistence(self):
        def mutate(d, j):
            checkout = next(s for s in j["steps"] if str(s.get("uses", "")).startswith("actions/checkout@"))
            checkout["with"]["persist-credentials"] = True
        self.reject(mutate)

    def test_excessive_permission(self):
        self.reject(lambda d, j: d["permissions"].update(contents="write"))

    def test_dynamic_secret_reference(self):
        self.reject(lambda d, j: j["steps"][-1]["env"].update(
            {"FOREIGN": "${{ secrets['THREADS_ACCESS_TOKEN'] }}"}))

    def test_entire_secret_context(self):
        self.reject(lambda d, j: j["steps"][-1]["env"].update(
            {"FOREIGN": "${{ toJSON(secrets) }}"}))

    def test_gate_reordered(self):
        def mutate(d, j):
            j["steps"][0], j["steps"][1] = j["steps"][1], j["steps"][0]
        self.reject(mutate)


class NativeCredentialCodecTests(unittest.TestCase):
    """Exercise the existing provisioning encoder against the real consumer."""
    @classmethod
    def setUpClass(cls):
        import ast
        import base64
        import importlib.util
        import time
        import zlib
        tree = ast.parse((ROOT / "tools/cortes_codeberg_tiktok_bootstrap.py").read_text(encoding="utf-8"))
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name in {"auth_cookies", "compact"}]
        namespace = {"json": json, "base64": base64, "zlib": zlib, "time": time}
        exec(compile(ast.Module(body=selected, type_ignores=[]), "<existing-codec>", "exec"), namespace)
        cls.encode = staticmethod(namespace["compact"])
        spec = importlib.util.spec_from_file_location(
            "native_runtime_consumer", ROOT / "tools/cortes_tiktok_lucasrosalem4_cloud_publish.py")
        cls.consumer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.consumer)

    def state(self):
        return {"cookies": [{"name": "sessionid", "domain": ".tiktok.com",
                             "value": "synthetic-not-a-credential", "expires": -1}],
                "origins": []}

    def decode(self, value):
        from unittest.mock import patch
        import os
        with patch.dict(os.environ, {VARIABLE: value}, clear=True):
            return self.consumer.state_from_secret()

    def test_existing_encoder_round_trips_through_actual_consumer(self):
        state = self.state()
        self.assertEqual(self.decode(self.encode(state)), state)

    def test_raw_recovery_json_requires_encoding_before_install(self):
        with self.assertRaises(self.consumer.SafeStop):
            self.decode(json.dumps(self.state()))

    def test_expired_recovery_session_is_not_installable(self):
        state = self.state()
        state["cookies"][0]["expires"] = 1
        with self.assertRaises(RuntimeError):
            self.encode(state)

    def test_existing_encoder_removes_other_domains_and_origins(self):
        state = self.state()
        state["cookies"].append({"name": "unrelated", "domain": ".example.org", "value": "synthetic"})
        state["origins"] = [{"origin": "https://example.org", "localStorage": []}]
        self.assertEqual(self.decode(self.encode(state)), self.state())


if __name__ == "__main__":
    unittest.main()
