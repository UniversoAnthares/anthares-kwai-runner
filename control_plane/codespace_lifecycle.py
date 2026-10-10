"""Minimal GitHub Codespaces lifecycle client for Anthares.

The user token is accepted only in memory. It is never persisted or returned in
result metadata. The client wakes an existing codespace for the target repository;
it does not create additional codespaces, which keeps quota use explicit.
"""
from __future__ import annotations

import json
import os
from typing import Callable
from urllib import error, parse, request

API_BASE = "https://api.github.com"
API_VERSION = "2026-03-10"
DEFAULT_REPOSITORY = "UniversoAnthares/anthares-kwai-runner"


class CodespaceLifecycleError(RuntimeError):
    def __init__(self, code: str, *, http_status: int | None = None):
        self.code = code
        self.http_status = http_status
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.http_status is None:
            return self.code
        return f"{self.code}:http={self.http_status}"


def _default_transport(method: str, path: str, token: str) -> tuple[int, dict]:
    if not token or not token.strip():
        raise CodespaceLifecycleError("codespaces_token_missing")
    req = request.Request(
        API_BASE + path,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "anthares-remote-publisher",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}
        return exc.code, payload


def _request_json(
    method: str,
    path: str,
    token: str,
    *,
    transport: Callable[[str, str, str], tuple[int, dict]] = _default_transport,
) -> dict:
    if not token or not token.strip():
        raise CodespaceLifecycleError("codespaces_token_missing")
    status, payload = transport(method, path, token)
    if status < 200 or status >= 300 or not isinstance(payload, dict):
        if status in {401, 403}:
            code = "codespaces_token_unauthorized"
        elif status == 402:
            code = "codespaces_quota_or_billing_blocked"
        elif status == 404:
            code = "codespace_not_found"
        else:
            code = "codespaces_api_error"
        raise CodespaceLifecycleError(code, http_status=status)
    return payload


def list_codespaces(
    token: str,
    *,
    transport: Callable[[str, str, str], tuple[int, dict]] = _default_transport,
) -> list[dict]:
    payload = _request_json("GET", "/user/codespaces?per_page=100", token, transport=transport)
    rows = payload.get("codespaces")
    if not isinstance(rows, list):
        raise CodespaceLifecycleError("codespaces_list_invalid")
    return [row for row in rows if isinstance(row, dict)]


def choose_codespace(rows: list[dict], repository: str = DEFAULT_REPOSITORY) -> dict:
    matches = []
    target = repository.lower().strip()
    for row in rows:
        repo = row.get("repository") or {}
        full_name = str(repo.get("full_name") or "").lower().strip()
        name = str(row.get("name") or "").strip()
        if full_name == target and name:
            matches.append(row)
    if not matches:
        raise CodespaceLifecycleError("codespace_for_repository_missing")
    matches.sort(key=lambda row: str(row.get("last_used_at") or row.get("updated_at") or ""), reverse=True)
    return matches[0]


def wake_existing_codespace(
    token: str,
    *,
    repository: str = DEFAULT_REPOSITORY,
    transport: Callable[[str, str, str], tuple[int, dict]] = _default_transport,
) -> dict:
    row = choose_codespace(list_codespaces(token, transport=transport), repository)
    name = str(row["name"])
    state = str(row.get("state") or "unknown")
    if state.lower() == "available":
        return {
            "repository": repository,
            "codespace_name": name,
            "action": "already_available",
            "state": state,
            "token_exported": False,
        }
    path = f"/user/codespaces/{parse.quote(name, safe='')}/start"
    started = _request_json("POST", path, token, transport=transport)
    return {
        "repository": repository,
        "codespace_name": name,
        "action": "start_requested",
        "state": str(started.get("state") or "starting"),
        "token_exported": False,
    }


def main() -> int:
    token = os.environ.get("ANTHARES_CODESPACES_TOKEN", "")
    repository = os.environ.get("ANTHARES_CODESPACE_REPOSITORY", DEFAULT_REPOSITORY)
    result = wake_existing_codespace(token, repository=repository)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
