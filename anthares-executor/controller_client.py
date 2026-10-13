"""Provider-neutral control-plane adapter. Never transmits login credentials or browser profiles."""
import json
import os
import urllib.error
import urllib.request

class ExecutorClient:
    def __init__(self, base_url=None, token=None, timeout=12):
        self.base = (base_url or os.environ["ANTHARES_EXECUTOR_URL"]).rstrip("/")
        self.token = token or os.environ["ANTHARES_EXECUTOR_TOKEN"]
        self.timeout = timeout
        if not self.base.startswith("https://") and not self.base.startswith("http://127.0.0.1:"):
            raise ValueError("Executor URL must use HTTPS (or loopback for local tests)")
        if not self.token:
            raise ValueError("Executor token is required")

    def request(self, method, path, data=None):
        payload = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(self.base + path, data=payload, method=method,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def health(self):
        return self.request("GET", "/health")

    def start_browser(self):
        return self.request("POST", "/v1/browser/start", {})

    def stop_browser(self):
        return self.request("POST", "/v1/browser/stop", {})

    def accept_lease(self, job_id, lease, generation):
        return self.request("POST", "/v1/jobs", {
            "id": job_id, "lease": lease, "generation": generation})

    def complete(self, job_id, lease, generation, result):
        from urllib.parse import quote
        return self.request("POST", "/v1/jobs/" + quote(job_id, safe="") + "/complete", {
            "lease": lease, "generation": generation, "result": result})

    def retrieve(self, job_id):
        from urllib.parse import quote
        return self.request("GET", "/v1/jobs/" + quote(job_id, safe=""))
