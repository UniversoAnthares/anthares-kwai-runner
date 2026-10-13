from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class Provider:
    name: str
    base_url: str


class ControlPlaneClient:
    """Sticky failover client.

    Jobs are mirrored to every reachable provider with the same idempotency key.
    Claiming stays on one provider until it is declared unhealthy. Once failover
    occurs, the client remains pinned to the backup until explicit failback.
    """

    def __init__(self, providers: list[Provider], token: str, timeout: float = 5.0):
        if not providers:
            raise ValueError("at_least_one_provider_required")
        self.providers = providers
        self.token = token
        self.timeout = timeout
        self.active_index = 0

    def _call(self, provider: Provider, method: str, path: str, body: Any | None = None):
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
        req = request.Request(
            provider.base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8")) if raw else None

    def healthy(self, provider: Provider) -> bool:
        try:
            req = request.Request(provider.base_url.rstrip("/") + "/health", method="GET")
            with request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status == 200 and bool(json.loads(resp.read().decode("utf-8")).get("ok"))
        except Exception:
            return False

    @property
    def active_provider(self) -> Provider:
        return self.providers[self.active_index]

    def enqueue(self, job: dict[str, Any]) -> dict[str, Any]:
        successes: list[tuple[str, dict[str, Any]]] = []
        failures: list[str] = []
        for provider in self.providers:
            try:
                status, payload = self._call(provider, "POST", "/v1/jobs", job)
                if status in (200, 201):
                    successes.append((provider.name, payload))
                else:
                    failures.append(provider.name)
            except Exception:
                failures.append(provider.name)
        if not successes:
            raise RuntimeError("all_control_planes_unreachable")
        return {"mirrored_to": [x[0] for x in successes], "failed": failures, "job": successes[0][1]["job"]}

    def claim(self, executor_id: str, kinds: list[str] | None = None, ttl_seconds: int = 120):
        order = list(range(self.active_index, len(self.providers))) + list(range(0, self.active_index))
        last_error: Exception | None = None
        for idx in order:
            provider = self.providers[idx]
            if idx != self.active_index and not self.healthy(provider):
                continue
            try:
                status, payload = self._call(
                    provider,
                    "POST",
                    "/v1/jobs/next",
                    {"executor_id": executor_id, "kinds": kinds or [], "ttl_seconds": ttl_seconds},
                )
                if status == 204:
                    return None
                if status == 200:
                    self.active_index = idx
                    payload["provider_name"] = provider.name
                    payload["provider_url"] = provider.base_url
                    return payload
            except error.HTTPError as exc:
                last_error = exc
                if exc.code == 503:
                    continue
            except Exception as exc:
                last_error = exc
                continue
        if last_error:
            raise RuntimeError(f"no_active_control_plane: {last_error}")
        return None

    def heartbeat(self, job: dict[str, Any], executor_id: str, ttl_seconds: int = 120):
        provider = Provider(job["provider_name"], job["provider_url"])
        return self._call(
            provider,
            "POST",
            f"/v1/jobs/{job['id']}/heartbeat",
            {
                "executor_id": executor_id,
                "lease_token": job["lease_token"],
                "lease_generation": job["lease_generation"],
                "ttl_seconds": ttl_seconds,
            },
        )[1]

    def complete(self, job: dict[str, Any], executor_id: str, result: dict[str, Any]):
        provider = Provider(job["provider_name"], job["provider_url"])
        return self._call(
            provider,
            "POST",
            f"/v1/jobs/{job['id']}/complete",
            {
                "executor_id": executor_id,
                "lease_token": job["lease_token"],
                "lease_generation": job["lease_generation"],
                "result": result,
            },
        )[1]

    def fail(self, job: dict[str, Any], executor_id: str, error_data: dict[str, Any]):
        provider = Provider(job["provider_name"], job["provider_url"])
        return self._call(
            provider,
            "POST",
            f"/v1/jobs/{job['id']}/fail",
            {
                "executor_id": executor_id,
                "lease_token": job["lease_token"],
                "lease_generation": job["lease_generation"],
                "error": error_data,
            },
        )[1]

    def failback(self, provider_name: str) -> None:
        for idx, provider in enumerate(self.providers):
            if provider.name == provider_name:
                if not self.healthy(provider):
                    raise RuntimeError("target_provider_unhealthy")
                self.active_index = idx
                return
        raise KeyError(provider_name)
