#!/usr/bin/env python3
"""AI-01 Groq capability audit (QA only).

Never reads storage, cookies, 9Router or WordPress secrets. The sole optional live
request requires an explicit operator flag and GROQ_API_KEY in the process environment.
No polling, retry, provider fallback, publishing or production state changes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import time
from urllib import error, request

MODEL = "openai/gpt-oss-20b"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
PRICE_PER_MILLION_INPUT_USD = 0.075
PRICE_PER_MILLION_OUTPUT_USD = 0.30
MAX_OUTPUT_TOKENS = 64
PRICE_CEILING_INPUT_TOKENS = 300
SYNTHETIC_PROMPT = (
    'Responda em português brasileiro e somente com JSON válido contendo '
    'exatamente {"soma":7,"idioma":"pt-BR","fonte":"sintetica"}. '
    'A resposta é uma verificação sintética sem conteúdo pessoal.'
)
PUBLIC_SOURCES = {
    "capability_price": "https://console.groq.com/docs/model/openai/gpt-oss-20b",
    "organization_limits": "https://console.groq.com/docs/rate-limits",
    "data_handling": "https://console.groq.com/docs/your-data",
}
RATE_HEADERS = (
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
    "retry-after",
)


def max_expected_cost_usd() -> float:
    return (
        PRICE_CEILING_INPUT_TOKENS * PRICE_PER_MILLION_INPUT_USD
        + MAX_OUTPUT_TOKENS * PRICE_PER_MILLION_OUTPUT_USD
    ) / 1_000_000


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * PRICE_PER_MILLION_INPUT_USD
        + output_tokens * PRICE_PER_MILLION_OUTPUT_USD
    ) / 1_000_000


def safe_headers(headers: dict) -> dict:
    lowered = {str(k).lower(): str(v) for k, v in headers.items()}
    return {key: lowered[key] for key in RATE_HEADERS if key in lowered}


def parse_result(status: int, payload: dict | None, headers: dict, elapsed_ms: int) -> dict:
    result = {
        "schema": "anthares.ai01.groq.capability.qa.v1",
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "groq",
        "model_requested": MODEL,
        "capability": "pt-BR structured JSON arithmetic, synthetic data only",
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "rate_limit_headers": safe_headers(headers),
        "quoted_price_usd_per_1m_tokens": {
            "input": PRICE_PER_MILLION_INPUT_USD,
            "output": PRICE_PER_MILLION_OUTPUT_USD,
        },
        "public_sources": PUBLIC_SOURCES,
        "data_class": "synthetic_only",
        "keys_exported": False,
        "calls_attempted": 1,
        "production_mutated": False,
        "upstream_quality_pass": False,
        "account_plan_verified": False,
        "account_permissions_verified": False,
        "account_spend_cap_verified": False,
        "account_quota_verified": False,
        "certification": "PARTIAL",
    }
    if status != 200 or not isinstance(payload, dict):
        result["reason"] = "no_valid_authenticated_success"
        return result
    usage = payload.get("usage")
    choices = payload.get("choices")
    if not isinstance(usage, dict) or not isinstance(choices, list) or not choices:
        result["reason"] = "missing_usage_or_choices"
        return result
    def nonnegative_int(value):
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    in_tokens, out_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
    if not nonnegative_int(in_tokens) or not nonnegative_int(out_tokens):
        result["reason"] = "invalid_usage"
        return result
    result["model_reported"] = payload.get("model")
    result["usage"] = {"input_tokens": in_tokens, "output_tokens": out_tokens}
    result["estimated_usage_cost_usd"] = estimate_cost_usd(in_tokens, out_tokens)
    result["price_is_estimate_not_invoice"] = True
    try:
        raw_text = choices[0]["message"]["content"]
        output = json.loads(raw_text)
    except (TypeError, ValueError, KeyError, IndexError):
        output = None
    valid = (
        isinstance(output, dict)
        and set(output) == {"soma", "idioma", "fonte"}
        and output["soma"] == 7
        and type(output["soma"]) is int
        and output["idioma"] == "pt-BR"
        and output["fonte"] == "sintetica"
        and payload.get("model") == MODEL
    )
    result["upstream_quality_pass"] = valid
    result["reason"] = (
        "account_entitlements_and_billing_unverified"
        if valid else "wrong_model_or_json_quality_failure"
    )
    return result


def single_live_call(api_key: str, max_budget_usd: float, timeout_s: int = 15) -> dict:
    if not api_key or len(api_key) < 16:
        raise ValueError("missing_authorized_credential")
    if not (0 < max_budget_usd <= 0.001):
        raise ValueError("budget_cap_out_of_range")
    if max_expected_cost_usd() > max_budget_usd:
        raise ValueError("conservative_budget_too_small")
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Retorne apenas JSON. Sem dados reais."},
            {"role": "user", "content": SYNTHETIC_PROMPT},
        ],
        "response_format": {"type": "json_object"},
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0,
        "stream": False,
    }).encode("utf-8")
    req = request.Request(
        ENDPOINT, data=body, method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    start = time.monotonic_ns()
    try:
        with request.urlopen(req, timeout=timeout_s) as response:
            raw = response.read(100_000)
            status, headers = response.status, dict(response.headers.items())
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                payload = None
    except error.HTTPError as exc:
        # Discard the remote error body; never copy request contents or credentials.
        status, headers, payload = exc.code, dict(exc.headers.items()), None
    except (error.URLError, TimeoutError):
        status, headers, payload = 0, {}, None
    elapsed = (time.monotonic_ns() - start) // 1_000_000
    return parse_result(status, payload, headers, int(elapsed))


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-01 Groq scoped capability audit")
    parser.add_argument("--live", action="store_true", help="one real request; never default")
    parser.add_argument("--authorized-call", action="store_true",
                        help="confirm real model request authorized for this upstream")
    parser.add_argument("--max-usd", type=float, default=0.0)
    args = parser.parse_args()
    if not args.live:
        print(json.dumps({
            "schema": "anthares.ai01.groq.capability.qa.v1",
            "certification": "NOT_TESTED",
            "model": MODEL,
            "sources": PUBLIC_SOURCES,
            "estimated_max_one_call_usd": max_expected_cost_usd(),
            "requires": [
                "authorized account-specific credential",
                "operator approval of request and account charge capability",
                "verified organization/project quota, spend cap and permissions",
                "one authenticated measured model response",
            ],
            "calls_attempted": 0,
        }, sort_keys=True))
        return 0
    if not args.authorized_call:
        parser.error("--live requires --authorized-call")
    try:
        result = single_live_call(os.environ.get("GROQ_API_KEY", ""), args.max_usd)
    except ValueError as exc:
        print(json.dumps({"certification": "NOT_TESTED", "reason": str(exc),
                          "calls_attempted": 0}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["upstream_quality_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
