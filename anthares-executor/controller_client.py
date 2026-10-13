"""Provider-neutral Anthares executor client.

Tokens remain in environment/configuration and are never serialized in job data.
"""
import json
import os
from urllib.parse import quote
import urllib.error
import urllib.request


class ExecutorClient:
    def __init__(self, base_url=None, token=None, timeout=20):
        self.base = (base_url or os.environ["ANTHARES_EXECUTOR_URL"]).rstrip("/")
        self.token = token or os.environ["ANTHARES_EXECUTOR_TOKEN"]
        self.timeout = timeout
        if not self.base.startswith("https://") and not self.base.startswith("http://127.0.0.1:"):
            raise ValueError("Executor URL must use HTTPS (or loopback for local tests)")
        if len(self.token) < 20:
            raise ValueError("Executor token must contain at least 20 characters")

    def request(self, method, path, data=None, authenticated=True):
        payload = json.dumps(data).encode() if data is not None else None
        headers = {"Content-Type": "application/json"}
        if authenticated:
            headers["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(self.base + path, data=payload, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode())
            except Exception:
                body = {"error": "http_error"}
            return exc.code, body

    def health(self):
        return self.request("GET", "/health", authenticated=False)

    def start_browser(self):
        return self.request("POST", "/v1/browser/start", {})

    def stop_browser(self):
        return self.request("POST", "/v1/browser/stop", {})

    def restore_profile(self):
        return self.request("POST", "/v1/profile/restore", {})

    def snapshot_profile(self):
        return self.request("POST", "/v1/profile/snapshot", {})

    def probe_kwai(self):
        return self.request("POST", "/v1/kwai/probe", {})

    def accept_lease(self, job_id, lease, generation):
        return self.request("POST", "/v1/jobs", {"id": job_id, "lease": lease, "generation": generation})

    def heartbeat(self, job_id, lease, generation):
        return self.request("POST", "/v1/jobs/" + quote(job_id, safe="") + "/heartbeat", {"lease": lease, "generation": generation})

    def complete(self, job_id, lease, generation, result):
        return self.request("POST", "/v1/jobs/" + quote(job_id, safe="") + "/complete", {"lease": lease, "generation": generation, "result": result})

    def retrieve(self, job_id):
        return self.request("GET", "/v1/jobs/" + quote(job_id, safe=""))
