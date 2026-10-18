#!/usr/bin/env python3
"""Fail-closed compatibility adapter: Cloudflare Kwai callbacks -> Neon fenced queue.

Only the canonical physical-first SYSTEM consumer invokes this module. Neon is the
sole publication lease authority after cutover. No automatic legacy fallback.
"""
from __future__ import annotations

import json
import os

from cortes_neon_queue_client import call

DEVICE = os.getenv("ANTHARES_DEVICE_ID", "DESKTOP-FTDK0HP")
OWNER = os.getenv("CORTES_QUEUE_OWNER", "physical_android:" + DEVICE)
TARGET = os.getenv("CORTES_QUEUE_TARGET", "kwai:lucasrosalem")


def _result(action: str, body: dict) -> tuple[int, dict]:
    try:
        result = call(action, body)
    except Exception as exc:
        return 503, {"ok": False, "error": "neon_transport_unavailable",
                     "detail": type(exc).__name__, "publication_allowed": False}
    return int(result.pop("http_status", 200 if result.get("ok") else 409)), result


def _evidence(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            if isinstance(decoded, dict):
                return decoded
        except (ValueError, TypeError):
            pass
    return {}


def signed_legacy_queue_call(path: str, payload: dict) -> tuple[int, dict]:
    operation = path.rsplit("/", 1)[-1]
    jobid = str(payload.get("id") or "")
    generation = payload.get("lease_generation")
    owner = str(os.getenv("KWAI_LEASE_OWNER") or OWNER)

    if operation == "lease":
        if payload.get("platform") != "kwai" or payload.get("executor") != "physical_android":
            return 400, {"ok": False, "error": "unexpected_executor_or_platform"}
        ttl = int(payload.get("ttl_seconds") or 3600)
        status, response = _result("lease", {
            "owner": OWNER, "target_key": TARGET,
            "lease_seconds": min(max(ttl, 90), 3600)
        })
        row = response.get("job")
        if status == 200 and row is not None:
            if row.get("target_key") != TARGET or not isinstance(row.get("payload"), dict):
                return 409, {"ok": False, "error": "unexpected_queue_job_shape"}
            # The legacy Android worker needs the callback credentials and clip URL.
            job = dict(row["payload"])
            job.update({"id": row["id"], "lease_generation": row["lease_generation"],
                        "lease_owner": row.get("lease_owner") or OWNER,
                        "target_key": row["target_key"]})
            response["job"] = job
        return status, response

    if not jobid:
        return 400, {"ok": False, "error": "missing_job_id"}
    if operation in ("started", "complete", "fail") and not generation:
        return 400, {"ok": False, "error": "missing_lease_generation"}

    base = {"id": jobid, "owner": owner, "lease_generation": generation}
    if operation == "started":
        return _result("start", base)
    if operation == "complete":
        evidence = _evidence(payload.get("confirmation_evidence"))
        remote_id = str(payload.get("remote_id") or "")
        if payload.get("confirmed") is not True or not evidence.get("kind") or not remote_id:
            return 409, {"ok": False, "error": "verified_publication_evidence_required"}
        return _result("confirm", {**base, "confirmation_evidence": evidence,
                                   "remote_id": remote_id})
    if operation == "fail":
        # A failed post-START operation is held UNCERTAIN by Neon; do not retry.
        return _result("fail", base)
    if operation == "reconcile":
        evidence = _evidence(payload.get("confirmation_evidence"))
        remote_id = str(payload.get("remote_id") or "")
        if payload.get("confirmed") is not True or not evidence.get("kind") or not remote_id:
            return 409, {"ok": False, "error": "reconciliation_evidence_required"}
        return _result("reconcile", {"id": jobid, "confirmation_evidence": evidence,
                                     "remote_id": remote_id})
    return 404, {"ok": False, "error": "unsupported_neon_queue_operation"}
