#!/usr/bin/env python3
"""CORTES shared Neon queue: safe routing around Vercel without duplicated posts.

All backends share exactly one PostgreSQL ledger. Before sending each write,
select a healthy backend; an uncertain *mutating* response is never replayed.
Only deterministic enqueue (same dedupe ID) and read-only pending can safely
try a second provider after a network error. Per-network auth/quotas are NOT
bypassed by failover; HTTP 401/403/409/429 always stop.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

AUDIENCE = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
PROVIDERS = (
    "https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/",
    AUDIENCE,
    "https://anthares-cortes-neon-edge-ha.anthares1.workers.dev/",
    "https://anthares-cortes-queue-ha.anthares1.workers.dev/",
)
ACTIONS = frozenset({"enqueue", "buffer-lease", "buffer-start", "buffer-fail",
                     "buffer-scheduled", "buffer-pending", "buffer-reconcile",
                     "personal-lease", "personal-start", "personal-fail",
                     "personal-accepted", "personal-confirmed"})
RETRYABLE = frozenset({"enqueue", "buffer-pending"})


class BackendUnavailable(RuntimeError):
    pass


def is_healthy(provider: str, timeout: int = 8) -> bool:
    url = provider.rstrip("/") + "?action=health"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "AntharesCortesQueueHA/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status, body = response.status, json.load(response)
        return status == 200 and body.get("ok") is True and (
            body.get("database_ok") is True or
            (body.get("backend") == "vercel-neon" and body.get("fencing") is True))
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, TimeoutError):
        return False


def post(action: str, payload: dict, get_oidc, *, timeout: int = 16) -> dict:
    if action not in ACTIONS:
        raise ValueError("CORTES_QUEUE_ACTION_NOT_ALLOWED")
    token = get_oidc()
    if not isinstance(token, str) or len(token) < 60:
        raise BackendUnavailable("CORTES_QUEUE_OIDC_UNAVAILABLE")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > 65536:
        raise ValueError("CORTES_QUEUE_PAYLOAD_TOO_LARGE")
    # Instagram and Pinterest use the already authorized Neon OIDC role;
    # do not try the Vercel endpoint first (its allowlist was LinkedIn-only).
    # This is an explicit preferred origin, NOT retrying after an HTTP 401.
    preferred = os.environ.get("CORTES_QUEUE_PRIMARY", "").strip().lower()
    if preferred:
        if preferred != "neon" or action not in ACTIONS:
            raise ValueError("CORTES_QUEUE_PRIMARY_UNSUPPORTED")
        if not (os.environ.get("GITHUB_ACTIONS") == "true" and
                os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted" and
                os.environ.get("RUNNER_OS") == "Linux"):
            raise BackendUnavailable("CORTES_QUEUE_NEON_REQUIRES_CLOUD")
        providers = tuple(sorted(PROVIDERS, key=lambda url: 0 if 'cortesqueue.compute.' in url else 1))
    else:
        providers = PROVIDERS
    for provider in providers:
        if not is_healthy(provider):
            continue
        target = provider.rstrip("/") + "?" + urllib.parse.urlencode({"action": action})
        request = urllib.request.Request(target, data=data, method="POST", headers={
            "Authorization": "Bearer " + token, "Content-Type": "application/json",
            "Accept": "application/json", "User-Agent": "AntharesCortesQueueHA/2.0",
        })
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.load(response)
            if not isinstance(result, dict):
                raise BackendUnavailable("CORTES_QUEUE_RESPONSE_INVALID")
            return result
        except urllib.error.HTTPError as error:
            if (500 <= error.code <= 599 or error.code == 404) and action in RETRYABLE:
                continue
            if 500 <= error.code <= 599:
                raise BackendUnavailable("CORTES_QUEUE_MUTATION_RESULT_UNCERTAIN") from None
            # Authorization, quota, CAS/lease and rate limits MUST be honored
            # for the destination even when another ingress is healthy.
            raise BackendUnavailable("CORTES_QUEUE_REJECTED_" + str(error.code)) from None
        except (TimeoutError, urllib.error.URLError, OSError, ValueError, BackendUnavailable):
            if action in RETRYABLE:
                continue
            raise BackendUnavailable("CORTES_QUEUE_MUTATION_RESULT_UNCERTAIN") from None
    raise BackendUnavailable("CORTES_QUEUE_ALL_PROVIDERS_UNAVAILABLE")
