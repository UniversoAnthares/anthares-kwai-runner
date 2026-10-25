"""Optional Anthares AI-04 circuit-bound adapter for the real local AI runner.

Only applies when a caller explicitly provides VERIFIED ProviderPolicy values.
Never creates credentials, authorizes payment, or advertises production readiness.
The consumer remains local diagnostics; WordPress cloud production is unchanged.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterable

from ai_hub.eligibility_breaker import (
    CircuitBreaker,
    NoEligibleProvider,
    ProviderPolicy,
    ProvidersTemporarilyUnavailable,
    UpstreamOutcomeError,
    dispatch,
)

TIMEOUT_STATES = frozenset({
    "RESPONSE_TIMEOUT", "MARKER_TIMEOUT", "RUNNER_TIMEOUT",
    "NETWORK_TIMEOUT", "HTTP_TIMEOUT",
})
# Preserve the status code for genuine HTTP results exposed by the runner.
STATUS_HTTP = {
    "PAYMENT_REQUIRED": 402,
    "RATE_LIMIT": 429,
    "HTTP_402": 402,
    "HTTP_429": 429,
    "UPSTREAM_ERROR": 503,
    "HTTP_503": 503,
}


def _provider_result_or_raise(raw: dict) -> dict:
    """Map a real runner's failure into the circuit's decision vocabulary."""
    if not isinstance(raw, dict):
        raise UpstreamOutcomeError(502)
    if raw.get("ok") is True and raw.get("response"):
        return raw
    status = str(raw.get("status", "UNKNOWN")).upper()
    if status in TIMEOUT_STATES:
        raise TimeoutError("upstream_timeout")
    numeric = raw.get("http_status")
    if isinstance(numeric, int) and 400 <= numeric <= 599:
        raise UpstreamOutcomeError(numeric)
    if status in STATUS_HTTP:
        raise UpstreamOutcomeError(STATUS_HTTP[status])
    if status.startswith("HTTP_") and status[5:].isdigit():
        raise UpstreamOutcomeError(int(status[5:]))
    # A failed/empty response is never a success and may not be retried blindly.
    raise UpstreamOutcomeError(502)


def execute_eligible_text(*, prompt: str, provider: str,
                          order: list[str], exclude: set[str],
                          policies: Iterable[ProviderPolicy],
                          breaker: CircuitBreaker | None,
                          timeout: int, response_timeout: int, envelope: bool,
                          run_once: Callable, log_path: Path,
                          append_log: Callable, prompt_hash: Callable) -> dict:
    started = time.monotonic()
    breaker = breaker if breaker is not None else CircuitBreaker()
    policy_list = list(policies)
    if any(not isinstance(policy, ProviderPolicy) for policy in policy_list):
        raise TypeError("verified_provider_policy_required")
    indexed = {p.name: p for p in policy_list}
    if len(indexed) != len(policy_list):
        raise ValueError("duplicate_provider_policy")
    ordered = [name for name in order if name in indexed and name not in exclude]
    if provider != "auto":
        ordered = [name for name in ordered if name == provider]
    selected = [indexed[name] for name in ordered]
    events = []

    def call(name: str):
        # Exactly one call per eligible candidate, no retries in this path.
        raw = run_once(name, prompt, timeout, response_timeout, envelope, False)
        status = str(raw.get("status", "INVALID_RESPONSE")) if isinstance(raw, dict) else "INVALID_RESPONSE"
        event = {"provider": name,
                 "ok": isinstance(raw, dict) and raw.get("ok") is True,
                 "status": status,
                 "attempt": 1,
                 "prompt_hash": prompt_hash(prompt),
                 "mode": "local-web-eligibility"}
        # append_log itself filters sensitive fields, never logs the prompt.
        append_log(log_path, event)
        events.append({"provider": name, "status": status, "ok": bool(event["ok"])})
        return _provider_result_or_raise(raw)

    try:
        result, selected_name, attempts = dispatch("text", selected, breaker, call)
    except NoEligibleProvider:
        outcome = "NO_ELIGIBLE_VERIFIED_PROVIDER"
    except ProvidersTemporarilyUnavailable:
        outcome = "NO_VERIFIED_UPSTREAM_RESPONSE"
    except UpstreamOutcomeError:
        outcome = "UPSTREAM_REJECTED"
    else:
        return {"ok": True, "provider": selected_name, "status": "SUCCESS",
                "response": str(result.get("response", "")),
                "runtime": "local-web", "elapsed_s": round(time.monotonic() - started, 3),
                "attempts": events, "verified_policy_required": True}
    return {"ok": False, "provider": None, "status": outcome, "response": "",
            "runtime": "local-web", "elapsed_s": round(time.monotonic() - started, 3),
            "attempts": events, "verified_policy_required": True}
