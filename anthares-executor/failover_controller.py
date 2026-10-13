"""Multi-provider Anthares executor controller.

Provider definitions reference token *environment variable names*; token values are
never accepted in JSON. The only implemented operation is a read-only Kwai probe.
No upload or publication action exists here.
"""
import json
import os
import threading
import time
from controller_client import ExecutorClient


class LeaseKeeper:
    def __init__(self, client, job_id, lease, generation, interval=45):
        self.client = client
        self.job_id = job_id
        self.lease = lease
        self.generation = generation
        self.interval = max(10, interval)
        self.stop_event = threading.Event()
        self.failed = None
        self.thread = None

    def __enter__(self):
        # Refresh once immediately so a newly accepted lease cannot silently age
        # while profile restore/browser startup is still in progress.
        try:
            status, body = self.client.heartbeat(self.job_id, self.lease, self.generation)
            if status != 200:
                self.failed = (status, body.get("error", "heartbeat_failed"))
                return self
        except Exception as exc:
            self.failed = (0, type(exc).__name__)
            return self

        def run():
            while not self.stop_event.wait(self.interval):
                try:
                    status, body = self.client.heartbeat(self.job_id, self.lease, self.generation)
                    if status != 200:
                        self.failed = (status, body.get("error", "heartbeat_failed"))
                        self.stop_event.set()
                except Exception as exc:
                    self.failed = (0, type(exc).__name__)
                    self.stop_event.set()
        self.thread = threading.Thread(target=run, name="anthares-lease-heartbeat", daemon=True)
        self.thread.start()
        return self

    def assert_alive(self):
        if self.failed:
            raise RuntimeError("lease_heartbeat_failed")

    def __exit__(self, *_):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)


class FailoverController:
    def __init__(self, providers=None, cooldown=60):
        self.providers = providers if providers is not None else self._load()
        self.cooldown = cooldown
        self.failures = {}
        if not self.providers:
            raise ValueError("no executors configured")

    @staticmethod
    def _load():
        raw = json.loads(os.environ.get("ANTHARES_EXECUTORS_JSON", "[]"))
        if not isinstance(raw, list):
            raise ValueError("ANTHARES_EXECUTORS_JSON must be a list")
        providers = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))[:64]
            url = str(item.get("url", ""))
            token_env = str(item.get("token_env", ""))
            if not name or not token_env or token_env not in os.environ:
                continue
            client = ExecutorClient(url, os.environ[token_env])
            providers.append({"name": name, "priority": int(item.get("priority", 100)), "client": client})
        return sorted(providers, key=lambda p: (p["priority"], p["name"]))

    def _mark_failure(self, provider):
        self.failures[provider["name"]] = time.monotonic() + self.cooldown

    def candidates(self):
        now = time.monotonic()
        ready, cooling = [], []
        for provider in self.providers:
            (ready if self.failures.get(provider["name"], 0) <= now else cooling).append(provider)
        return ready or cooling

    def select(self):
        evidence = []
        for provider in self.candidates():
            try:
                status, health = provider["client"].health()
                ok = status == 200 and health.get("ok") is True
                evidence.append({"name": provider["name"], "healthy": ok, "chromium_ready": bool(health.get("chromium_ready")) if ok else False})
                if ok:
                    return provider, evidence, health
            except Exception:
                evidence.append({"name": provider["name"], "healthy": False, "error": "unreachable"})
            self._mark_failure(provider)
        return None, evidence, None

    def execute_readonly_kwai_probe(self, job_id, lease, generation):
        provider, providers, health = self.select()
        if provider is None:
            return {"ok": False, "error": "no_healthy_executor", "providers": providers}
        client = provider["client"]
        name = provider["name"]
        accepted = False
        browser_started = False
        result = {"ok": False, "executor": name, "providers": providers, "read_only": True}
        try:
            status, body = client.accept_lease(job_id, lease, generation)
            if status not in (200, 201):
                return {**result, "error": body.get("error", "lease_rejected")}
            accepted = True
            with LeaseKeeper(client, job_id, lease, generation) as keeper:
                keeper.assert_alive()
                if health.get("encrypted_profile_store_configured"):
                    status, restored = client.restore_profile()
                    keeper.assert_alive()
                    if status != 200 or not restored.get("ok"):
                        raise RuntimeError("profile_restore_failed")
                    result["profile_generation"] = restored.get("generation")
                status, started = client.start_browser()
                keeper.assert_alive()
                if status != 200 or not started.get("ok"):
                    raise RuntimeError("browser_start_failed")
                browser_started = True
                status, probe = client.probe_kwai()
                keeper.assert_alive()
                if status != 200 or not probe.get("ok"):
                    raise RuntimeError("kwai_probe_failed")
                result.update({
                    "ok": True,
                    "identity_verified": bool(probe.get("identity_verified")),
                    "upload_surface_verified": bool(probe.get("upload_surface_verified")),
                    "session_state": probe.get("session_state", "unknown"),
                    "evidence": probe.get("evidence", {}),
                })
        except Exception as exc:
            self._mark_failure(provider)
            result["ok"] = False
            result["error"] = str(exc)[:80]
        finally:
            if browser_started:
                try:
                    client.stop_browser()
                except Exception:
                    result["browser_stop_warning"] = True
                if result.get("ok") and health.get("encrypted_profile_store_configured"):
                    try:
                        status, snap = client.snapshot_profile()
                        if status == 200 and snap.get("ok"):
                            result["snapshot_generation"] = snap.get("generation")
                        else:
                            result["snapshot_warning"] = True
                    except Exception:
                        result["snapshot_warning"] = True
            if accepted:
                safe_result = {k: v for k, v in result.items() if k not in {"providers", "evidence"}}
                try:
                    client.complete(job_id, lease, generation, safe_result)
                except Exception:
                    result["completion_warning"] = True
        return result


def configured_provider_names():
    try:
        return [p["name"] for p in FailoverController().providers]
    except Exception:
        return []
