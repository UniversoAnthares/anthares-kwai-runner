#!/usr/bin/env python3
"""Fail-closed CI candidate selector. No API calls, secrets, build dispatch, or retries."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
from pathlib import Path

SOURCE_SHA = re.compile(r"^[a-f0-9]{40}$")
AMBIGUOUS = {"timeout", "unknown", "ambiguous", "mutation_started"}
CONFIRMED = {"http500", "confirmed_failure", "quota_exceeded", "provider_unavailable"}


def recent(when, now, max_age_seconds=600):
    if not isinstance(when, str):
        return False
    try:
        stamp = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    except ValueError:
        return False
    if stamp.tzinfo is None:
        return False
    age = (now - stamp.astimezone(dt.timezone.utc)).total_seconds()
    return 0 <= age <= max_age_seconds


def choose(routing, recorded, live, *, source_sha, previous=None,
           outcome="none", mutation_started=False, now=None):
    if not SOURCE_SHA.fullmatch(source_sha or ""):
        return {"action": "STOP", "reason": "INVALID_SOURCE_SHA"}
    if mutation_started:
        return {"action": "STOP", "reason": "MUTATION_BOUNDARY_RECONCILE"}
    order = routing.get("ci_execution", {}).get("priority", [])
    if not isinstance(order, list) or not order or any(not isinstance(p, str) for p in order) or len(order) != len(set(order)):
        return {"action": "STOP", "reason": "INVALID_ORDER"}
    if previous is not None:
        if previous not in order:
            return {"action": "STOP", "reason": "UNKNOWN_PREVIOUS_PROVIDER"}
        if outcome in AMBIGUOUS:
            return {"action": "STOP", "reason": "UNCERTAIN_RESULT_RECONCILE"}
        if outcome not in CONFIRMED:
            return {"action": "STOP", "reason": "FAILURE_NOT_CONFIRMED"}
        start = order.index(previous) + 1
    else:
        if outcome != "none":
            return {"action": "STOP", "reason": "MISSING_PREVIOUS_PROVIDER"}
        start = 0
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        return {"action": "STOP", "reason": "TIMEZONE_REQUIRED"}
    retired = set(recorded.get("rules", {}).get("retired_never_route", []))
    for name in order[start:]:
        if name in retired:
            continue
        meta = routing.get("providers", {}).get(name)
        state = recorded.get("providers", {}).get(name)
        proof = live.get(name)
        if not all(isinstance(x, dict) for x in (meta, state, proof)):
            continue
        if meta.get("active") is not True or meta.get("ci_eligible") is not True or state.get("eligible") is not True:
            continue
        if any(proof.get(k) is not True for k in ("healthy", "ready", "authenticated", "free_quota_ok", "runner_available")):
            continue
        if proof.get("source_sha") != source_sha or not proof.get("successful_hosted_run_id"):
            continue
        if not recent(proof.get("observed_at_utc"), now):
            continue
        return {"action": "SELECT_ONLY", "provider": name, "reason": "FRESH_VERIFIED", "dispatched": False}
    return {"action": "NONE", "reason": "NO_FRESH_ELIGIBLE_PROVIDER", "dispatched": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("routing", "status", "live"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--previous")
    parser.add_argument("--outcome", default="none")
    parser.add_argument("--mutation-started", action="store_true")
    args = parser.parse_args()
    try:
        documents = [json.loads(getattr(args, k).read_text(encoding="utf-8")) for k in ("routing", "status", "live")]
        if not all(isinstance(x, dict) for x in documents):
            raise ValueError("JSON objects required")
        result = choose(*documents, source_sha=args.source_sha, previous=args.previous,
                        outcome=args.outcome, mutation_started=args.mutation_started)
    except (ValueError, TypeError, OSError, KeyError) as exc:
        result = {"action": "STOP", "reason": "INVALID_INPUT", "detail": type(exc).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("action") == "SELECT_ONLY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
