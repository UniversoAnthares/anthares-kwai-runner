#!/usr/bin/env python3
"""Unified Anthares AI orchestrator.

Local development/runtime adapter for the five PROVEN isolated web providers:
Claude, Grok, Gemini, Perplexity and Manus.

The normal Anthares production site must not depend on this file or on the user's
PC. Production WordPress uses anthares-ai-hub cloud providers. This CLI exists for
local development, diagnostics, controlled fallback tests and optional operator
workflows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
DEFAULT_ORDER = ["claude", "grok", "gemini", "perplexity", "manus"]
PROVIDERS = set(DEFAULT_ORDER)
RETRYABLE = {
    "DESKTOP_CREATE_FAILED",
    "CHROME_LAUNCH_FAILED",
    "CDP_NOT_READY",
    "CLOUDFLARE_CHALLENGE",
    "RESPONSE_TIMEOUT",
    "MARKER_TIMEOUT",
    "RUNNER_TIMEOUT",
    "RUNNER_CRASH",
    "INVALID_JSON",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def parse_order(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_ORDER)
    out = []
    for raw in value.split(","):
        name = raw.strip().lower()
        if not name:
            continue
        if name not in PROVIDERS:
            raise ValueError(f"unknown provider in order: {name}")
        if name not in out:
            out.append(name)
    if not out:
        raise ValueError("provider order cannot be empty")
    return out


def parse_names(value: str | None) -> set[str]:
    if not value:
        return set()
    names = {x.strip().lower() for x in value.split(",") if x.strip()}
    invalid = names - PROVIDERS
    if invalid:
        raise ValueError("unknown providers: " + ", ".join(sorted(invalid)))
    return names


def build_envelope(prompt: str) -> tuple[str, str, str]:
    token = uuid.uuid4().hex[:12]
    start = f"ANTHARES_RESPONSE_START_{token}"
    end = f"ANTHARES_RESPONSE_END_{token}"
    wrapped = (
        "Siga a solicitação do usuário abaixo. Não repita nem explique estas instruções de integração.\n\n"
        "SOLICITAÇÃO DO USUÁRIO:\n"
        f"{prompt}\n\n"
        "FORMATO OBRIGATÓRIO: escreva o marcador inicial abaixo como a primeira linha; depois responda de fato à solicitação; escreva o marcador final como a última linha.\n"
        f"{start}\n{end}"
    )
    return wrapped, start, end


def strip_envelope(text: str, start: str, end: str) -> str:
    if not isinstance(text, str):
        return ""
    a = text.rfind(start)
    if a < 0:
        return ""
    a += len(start)
    b = text.find(end, a)
    if b < 0:
        return ""
    return text[a:b].strip()


def default_log_path() -> Path:
    override = os.environ.get("ANTHARES_AI_LOG")
    if override:
        return Path(override)
    return Path.home() / "AntharesWork" / "logs" / "anthares-ai-runner.jsonl"


def append_log(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = {
        "ts": now_iso(),
        "provider": event.get("provider"),
        "status": event.get("status"),
        "ok": bool(event.get("ok")),
        "elapsed_s": event.get("elapsed_s"),
        "attempt": event.get("attempt"),
        "prompt_hash": event.get("prompt_hash"),
        "mode": event.get("mode"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, ensure_ascii=False) + "\n")


def invoke_runner(provider: str, prompt: str, start: str | None, end: str | None,
                  timeout: int, response_timeout: int) -> dict:
    """Invoke low-level runners in-process to avoid nested Python launch restrictions."""
    try:
        if provider == "claude":
            import claude_hidden_runner as runner
            return runner.run_once(
                prompt,
                runner.DEFAULT_PROFILE,
                runner.DEFAULT_CHROME,
                timeout,
                response_timeout,
                None,
            )
        import hidden_chat_runner as runner
        return runner.run(
            provider,
            prompt,
            timeout=timeout,
            expect=start,
            expect_end=end,
            response_timeout=response_timeout,
        )
    except Exception as exc:
        return {
            "provider": provider,
            "ok": False,
            "status": "RUNNER_CRASH",
            "response": "",
            "elapsed_s": 0.0,
            "error_type": type(exc).__name__,
        }


def normalize(provider: str, raw: dict, start: str | None, end: str | None) -> dict:
    status = str(raw.get("status") or "UNKNOWN")
    response = str(raw.get("response") or "")
    ok = bool(raw.get("ok"))

    if start and end:
        parsed = strip_envelope(response, start, end)
        # Generic runner already strips the envelope. Claude returns the whole assistant block.
        if provider != "claude" and ok and response and not parsed:
            parsed = response
        if provider == "claude":
            if parsed:
                response = parsed
            else:
                ok = False
                status = "ENVELOPE_MISSING"
                response = ""
        elif ok:
            response = parsed or response

    return {
        "provider": provider,
        "ok": ok,
        "status": status,
        "response": response.strip(),
        "elapsed_s": raw.get("elapsed_s"),
        "url": raw.get("url"),
        "title": raw.get("title"),
    }


def run_once(provider: str, user_prompt: str, timeout: int, response_timeout: int,
             envelope: bool = True, simulate_failure: bool = False) -> dict:
    if simulate_failure:
        return {
            "provider": provider,
            "ok": False,
            "status": "SIMULATED_FAILURE",
            "response": "",
            "elapsed_s": 0.0,
        }

    if envelope:
        prompt, start, end = build_envelope(user_prompt)
    else:
        prompt, start, end = user_prompt, None, None

    raw = invoke_runner(provider, prompt, start, end, timeout, response_timeout)
    return normalize(provider, raw, start, end)


def run_with_retry(provider: str, prompt: str, timeout: int, response_timeout: int,
                   retries: int, envelope: bool, simulate_failure: bool,
                   log_path: Path) -> tuple[dict, list[dict]]:
    attempts = []
    total = retries + 1
    for idx in range(total):
        result = run_once(
            provider, prompt, timeout, response_timeout,
            envelope=envelope,
            simulate_failure=simulate_failure and idx == 0,
        )
        event = dict(result)
        event["attempt"] = idx + 1
        event["prompt_hash"] = prompt_hash(prompt)
        event["mode"] = "local-web"
        append_log(log_path, event)
        attempts.append(event)
        if result.get("ok"):
            return result, attempts
        if result.get("status") not in RETRYABLE:
            break
    return attempts[-1], attempts


def execute(prompt: str, provider: str = "auto", order: list[str] | None = None,
            exclude: set[str] | None = None, simulate_failures: set[str] | None = None,
            retries: int = 0, timeout: int = 90, response_timeout: int = 60,
            envelope: bool = True, log_path: Path | None = None) -> dict:
    started = time.time()
    order = list(order or DEFAULT_ORDER)
    exclude = set(exclude or ())
    simulate_failures = set(simulate_failures or ())
    log_path = log_path or default_log_path()

    candidates = [provider] if provider != "auto" else [p for p in order if p not in exclude]
    if provider != "auto" and provider in exclude:
        candidates = []

    all_attempts = []
    for name in candidates:
        result, attempts = run_with_retry(
            name, prompt, timeout, response_timeout, retries, envelope,
            name in simulate_failures, log_path,
        )
        all_attempts.extend(attempts)
        if result.get("ok"):
            return {
                "ok": True,
                "provider": name,
                "status": "SUCCESS",
                "response": result.get("response", ""),
                "runtime": "local-web",
                "elapsed_s": round(time.time() - started, 2),
                "attempts": all_attempts,
            }

    return {
        "ok": False,
        "provider": None,
        "status": "ALL_FAILED" if candidates else "NO_CANDIDATE",
        "response": "",
        "runtime": "local-web",
        "elapsed_s": round(time.time() - started, 2),
        "attempts": all_attempts,
    }


def health(provider: str, order: list[str], timeout: int, response_timeout: int,
           log_path: Path) -> dict:
    targets = order if provider == "auto" else [provider]
    rows = []
    for name in targets:
        marker = f"HEALTH_{name.upper()}_{uuid.uuid4().hex[:8]}"
        prompt = "Retorne exatamente o texto a seguir, sem explicaÃ§Ãµes adicionais: " + marker
        row = execute(
            prompt, provider=name, retries=0, timeout=timeout,
            response_timeout=response_timeout, envelope=True, log_path=log_path,
        )
        row["expected"] = marker
        row["matches_expected"] = marker in row.get("response", "")
        row["ok"] = bool(row.get("ok") and row["matches_expected"])
        rows.append(row)
    return {
        "ok": all(r.get("ok") for r in rows),
        "status": "SUCCESS" if all(r.get("ok") for r in rows) else "HEALTH_FAILED",
        "runtime": "local-web",
        "providers": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["auto"] + DEFAULT_ORDER, default="auto")
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--order", help="comma-separated provider order")
    ap.add_argument("--exclude", help="comma-separated providers")
    ap.add_argument("--simulate-failure", help="comma-separated providers; testing only")
    ap.add_argument("--retries", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--response-timeout", type=int, default=60)
    ap.add_argument("--raw", action="store_true", help="disable response envelope")
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--log-file")
    args = ap.parse_args()

    try:
        order = parse_order(args.order)
        exclude = parse_names(args.exclude)
        simulated = parse_names(args.simulate_failure)
    except ValueError as exc:
        ap.error(str(exc))

    log_path = Path(args.log_file) if args.log_file else default_log_path()
    if args.health:
        result = health(args.provider, order, args.timeout, args.response_timeout, log_path)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("ok") else 2

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not prompt:
        ap.error("use --prompt, --prompt-file, or --health")

    result = execute(
        prompt,
        provider=args.provider,
        order=order,
        exclude=exclude,
        simulate_failures=simulated,
        retries=max(0, args.retries),
        timeout=max(10, args.timeout),
        response_timeout=max(10, args.response_timeout),
        envelope=not args.raw,
        log_path=log_path,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
